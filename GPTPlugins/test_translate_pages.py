from datetime import date
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from wagtail.models import Locale, Page, Revision, Site
from wagtail_localize.models import StringTranslation, Translation, TranslationSource
from wagtail_localize.strings import StringValue

from blog.models import BlogIndexPage, BlogPage
from flex.models import Engineer
from home.models import HomePage


class BadTranslationTests(SimpleTestCase):
    def test_prompt_leak_predicate(self):
        from GPTPlugins.management.commands.translate_pages import is_bad_translation

        for text in ('Here are the translated paragraphs:\n\n0: stars',
                     'TRANSLATED PARAGRAPHS', '0: stars', '  12: stars',
                     'Stars over the village.&lt;b&gt;', '&lt;/b&gt;<br/>1: the second line',
                     'First line<br/>2: second line'):
            with self.subTest(text=text):
                self.assertTrue(is_bad_translation(text))
        for text in ('Stars above a fictional village', 'Chapter 12: stars', '2026 stars'):
            with self.subTest(text=text):
                self.assertFalse(is_bad_translation(text))


class TranslatePagesTransactionTests(TransactionTestCase):
    def test_translator_runs_without_an_open_transaction(self):
        source_locale, _ = Locale.objects.get_or_create(language_code='zh-hans')
        target_locale, _ = Locale.objects.get_or_create(language_code='en')
        root = Page.add_root(instance=Page(title='Root', slug='root', locale=source_locale))
        page = root.add_child(instance=HomePage(
            title='星光笔记', slug='notebook', banner='虚构的村庄', locale=source_locale))

        def translate(source, target, strings):
            self.assertFalse(connection.in_atomic_block)
            return {string: StringValue.from_translated_html(f'Translated {string.data}')
                    for string in strings}

        with patch('GPTPlugins.models.GeminiTranslator.translate', side_effect=translate) as translator:
            call_command('translate_pages', locale=[target_locale.language_code],
                         page=[page.pk], stdout=StringIO())
        translator.assert_called_once()
        self.assertEqual(page.get_translation(target_locale).title, 'Translated 星光笔记')


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class TranslatePagesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        # Remove Wagtail's initial welcome page so the whole source tree is fictional.
        Page.objects.filter(depth=2).delete()
        self.zh = Locale.get_default()
        self.en = Locale.objects.create(language_code='en')
        self.ja = Locale.objects.create(language_code='ja')
        self.home = Page.get_first_root_node().add_child(instance=HomePage(
            title='星光笔记', slug='notebook', banner='虚构的村庄', locale=self.zh))
        Site.objects.all().delete()
        Site.objects.create(hostname='testserver', root_page=self.home, is_default_site=True)
        self.section = self.home.add_child(instance=BlogIndexPage(title='故事', slug='stories'))
        self.post = self.section.add_child(instance=BlogPage(
            title='纸船', slug='paper-boat', date=date(2026, 1, 1),
            body='<p>纸船漂过虚构的村庄。</p>', cover_image='covers/fictional.png',
            notify_subscribers=True))
        self.engineer = self.section.add_child(instance=Engineer(
            title='星图', slug='star-map', date=date(2026, 1, 2),
            content=[{'type': 'full_richtext', 'value': '<p>绘制一张虚构的星图。</p>'}],
            cover_image='covers/fictional-map.png', notify_subscribers=True))
        translator = patch('GPTPlugins.models.GeminiTranslator.translate', side_effect=self.translate)
        self.translate_mock = translator.start()
        self.addCleanup(translator.stop)
        newsletter = patch('blog.models.send_emails.delay')
        self.newsletter = newsletter.start()
        self.addCleanup(newsletter.stop)

    def translate(self, source_locale, target_locale, strings):
        return {string: StringValue.from_translated_html(f'Translated {target_locale.language_code} {string.data}')
                for string in strings}

    def run_command(self, **options):
        from GPTPlugins.management.commands.translate_pages import translate_page

        def commit_page(*args):
            # Match the real command's per-page commits, even inside TestCase's
            # outer transaction. Publishing parents after children is not equivalent.
            with self.captureOnCommitCallbacks(execute=True):
                return translate_page(*args)

        output = StringIO()
        with patch('GPTPlugins.management.commands.translate_pages.translate_page', side_effect=commit_page):
            call_command('translate_pages', stdout=output, **options)
        return output.getvalue()

    def target(self, page, locale=None):
        return page.get_translation(locale or self.en).specific

    def test_missing_tree_is_translated_and_published_in_depth_first_order(self):
        output = self.run_command()
        self.assertEqual(self.translate_mock.call_count, 8)
        for locale in (self.en, self.ja):
            for page in (self.home, self.section, self.post, self.engineer):
                target = self.target(page, locale)
                self.assertTrue(target.live)
                self.assertEqual(target.title, f'Translated {locale.language_code} {page.title}')
                if page.depth > 2:
                    self.assertEqual(target.get_parent().pk, self.target(page.get_parent(), locale).pk)
            self.assertIn('Translated ' + locale.language_code, self.target(self.post, locale).body)
            self.assertIn('Translated ' + locale.language_code,
                          self.target(self.engineer, locale).content[0].value.source)
        self.assertTrue(StringTranslation.objects.exists())
        self.assertFalse(StringTranslation.objects.exclude(translation_type='machine', tool_name='Gemini').exists())
        self.assertIn('published=8', output)
        self.assertEqual(self.target(self.post).cover_image.name, self.post.cover_image.name)
        self.assertEqual(self.target(self.engineer).cover_image.name, self.engineer.cover_image.name)

    def test_complete_translation_is_skipped_without_calls_or_revisions(self):
        self.run_command(locale=['en'])
        self.translate_mock.reset_mock()
        revisions = Revision.objects.count()
        output = self.run_command(locale=['en'])
        self.translate_mock.assert_not_called()
        self.assertEqual(Revision.objects.count(), revisions)
        self.assertIn('skipped=4', output)

    def test_published_translations_render_with_translated_content(self):
        self.run_command()
        for locale in (self.en, self.ja):
            for page in (self.home, self.section, self.post, self.engineer):
                target = self.target(page, locale)
                for suffix in ('', '?type=share'):
                    with self.subTest(locale=locale.language_code, page=page.pk, suffix=suffix):
                        response = self.client.get(target.url + suffix)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(response.context['page'].title, target.title)
                        # Home deliberately renders fixed site branding; its translated
                        # sections appear in metadata. Detail/index pages render titles.
                        if page == self.home:
                            self.assertContains(response, self.target(self.section, locale).title)
                        else:
                            self.assertContains(response, target.title)
                        if page in (self.post, self.engineer):
                            self.assertContains(response, 'Translated ' + locale.language_code)
                            self.assertEqual(target.cover_image.name, page.cover_image.name)
                            if suffix:
                                self.assertContains(response, target.cover_image.url)
                            else:
                                self.assertContains(response, '<meta property="og:image" content="https://testserver/static/og-default.jpg">')
                                self.assertNotContains(response, f'<meta property="og:image" content="https://testserver{target.cover_image.url}">')

    def test_translating_a_site_root_clears_the_root_paths_cache(self):
        with patch('GPTPlugins.management.commands.translate_pages.Site.clear_site_root_paths_cache') as clear:
            self.run_command(locale=['en'], page=[self.home.pk])
            clear.assert_called()

    def test_bad_strings_are_deleted_and_retranslated(self):
        self.run_command(locale=['en'])
        strings = StringTranslation.objects.filter(locale=self.en, context__path='title').order_by('pk')
        bad_ids = []
        for string, data in zip(strings, ['Here are the translated paragraphs:\n\n0: stars', '12: stars']):
            string.data = data
            string.save()
            bad_ids.append(string.pk)
        self.translate_mock.reset_mock()
        self.run_command(locale=['en'])
        self.assertEqual(self.translate_mock.call_count, 2)
        self.assertFalse(StringTranslation.objects.filter(pk__in=bad_ids).exists())
        self.assertEqual(self.target(self.home).title, 'Translated en ' + self.home.title)

    def test_dry_run_has_no_api_calls_or_database_writes(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as queries:
            output = self.run_command(dry_run=True)
        self.translate_mock.assert_not_called()
        writes = [q['sql'] for q in queries if q['sql'].lstrip().split()[0].upper()
                  in {'INSERT', 'UPDATE', 'DELETE', 'REPLACE'}]
        self.assertEqual(writes, [])
        self.assertFalse(TranslationSource.objects.exists())
        self.assertIn('strings=', output)
        self.assertIn('characters=', output)
        self.assertNotIn(self.post.title, output)
        self.assertNotIn('纸船漂过', output)

    def test_no_publish_creates_drafts_and_default_run_publishes_them(self):
        self.run_command(locale=['en'], no_publish=True)
        for page in (self.home, self.section, self.post, self.engineer):
            self.assertFalse(self.target(page).live)
        self.translate_mock.reset_mock()
        self.run_command(locale=['en'])
        self.translate_mock.assert_not_called()
        self.assertTrue(self.target(self.post).live)
        self.assertTrue(self.target(self.engineer).live)

    def test_publish_never_sends_newsletter_even_from_flagged_aliases(self):
        for page in (self.home, self.section, self.post, self.engineer):
            page.copy_for_translation(self.en, alias=True)
        self.run_command(locale=['en'])
        self.newsletter.assert_not_called()
        self.assertEqual(len(mail.outbox), 0)
        for page in (self.post, self.engineer):
            page.refresh_from_db()
            self.assertTrue(page.notify_subscribers)
            target = self.target(page)
            self.assertIsNone(target.alias_of_id)
            self.assertFalse(target.notify_subscribers)
            self.assertFalse(target.latest_revision.content['notify_subscribers'])

    def test_api_failure_rolls_back_source_translation_and_target(self):
        self.translate_mock.side_effect = RuntimeError('Fictional API failure')
        before = Page.objects.count()
        with self.assertRaisesRegex(RuntimeError, 'Fictional API failure'):
            self.run_command(locale=['en'], page=[self.post.pk])
        self.assertEqual(Page.objects.count(), before)
        self.assertFalse(Translation.objects.exists())
        self.assertFalse(TranslationSource.objects.exists())
        self.assertFalse(StringTranslation.objects.exists())
        self.newsletter.assert_not_called()

    def test_latest_source_and_synchronized_covers_are_used(self):
        self.run_command(locale=['en'])
        self.post.body = '<p>纸船抵达另一座虚构的小岛。</p>'
        self.post.cover_image = 'covers/fictional-new.png'
        self.post.save()
        self.translate_mock.reset_mock()
        self.run_command(locale=['en'])
        self.translate_mock.assert_called_once()
        target = self.target(self.post)
        self.assertIn('纸船抵达另一座虚构的小岛。', target.body)
        self.assertEqual(target.cover_image.name, 'covers/fictional-new.png')
        self.post.cover_image = 'covers/fictional-newer.png'
        self.post.save()
        self.translate_mock.reset_mock()
        self.run_command(locale=['en'])
        self.translate_mock.assert_not_called()
        self.assertEqual(self.target(self.post).cover_image.name, 'covers/fictional-newer.png')

    def test_locale_page_and_limit_filters(self):
        output = self.run_command(locale=['en', 'ja'], page=[self.post.pk, self.engineer.pk], limit=1)
        self.assertEqual(self.translate_mock.call_count, 2)
        self.assertTrue(self.target(self.post).live)
        self.assertTrue(self.target(self.post, self.ja).live)
        self.assertFalse(self.engineer.get_translations().exists())
        self.assertIn('published=2', output)

    def test_draft_source_is_excluded_and_disabled_translation_is_enabled(self):
        self.engineer.live = False
        self.engineer.save()
        self.run_command(locale=['en'])
        Translation.objects.update(enabled=False)
        self.translate_mock.reset_mock()
        self.run_command(locale=['en'])
        self.assertFalse(Translation.objects.filter(enabled=False).exists())
        self.translate_mock.assert_not_called()
        self.assertFalse(self.engineer.get_translations().exists())

    def test_repeated_richtext_strings_share_one_translation(self):
        self.post.body = '<p>相同的虚构段落。</p><p>相同的虚构段落。</p>'
        self.post.save()
        self.run_command(locale=['en'], page=[self.post.pk])
        self.assertEqual(self.target(self.post).body.count('Translated en 相同的虚构段落。'), 2)
        self.assertEqual(StringTranslation.objects.filter(
            locale=self.en, context__object_id=self.post.translation_key,
            context__path='body').count(), 1)

    def test_invalid_stored_translation_is_never_reported_as_complete(self):
        from django.core.management.base import CommandError

        self.run_command(locale=['en'])
        StringTranslation.objects.filter(locale=self.en, context__object_id=self.post.translation_key).update(
            has_error=True)
        self.translate_mock.reset_mock()
        with self.assertRaisesRegex(CommandError, 'incomplete translation'):
            self.run_command(locale=['en'], page=[self.post.pk])
        with self.assertRaisesRegex(CommandError, 'incomplete translation'):
            self.run_command(locale=['en'], page=[self.post.pk], dry_run=True)
        self.translate_mock.assert_not_called()

    def test_partial_api_result_rolls_back_strings_and_alias_conversion(self):
        for page in (self.home, self.section, self.post):
            page.copy_for_translation(self.en, alias=True)
        target = self.target(self.post)
        self.translate_mock.side_effect = lambda source, target, strings: {
            next(iter(strings)): StringValue.from_plaintext('Fictional partial result')}
        with self.assertRaises(KeyError):
            self.run_command(locale=['en'], page=[self.post.pk])
        target.refresh_from_db()
        self.assertIsNotNone(target.alias_of_id)
        self.assertEqual(target.title, self.post.title)
        self.assertFalse(StringTranslation.objects.exists())
        self.assertFalse(TranslationSource.objects.exists())
        self.newsletter.assert_not_called()

    def test_no_publish_converts_live_alias_to_draft(self):
        for page in (self.home, self.section, self.post):
            page.copy_for_translation(self.en, alias=True)
        self.run_command(locale=['en'], page=[self.post.pk], no_publish=True)
        target = self.target(self.post)
        self.assertFalse(target.live)
        self.assertIsNone(target.alias_of_id)
        self.assertEqual(target.latest_revision.content['title'], 'Translated en ' + self.post.title)
        self.newsletter.assert_not_called()

    def test_no_publish_preserves_existing_live_content_and_saves_new_draft(self):
        self.run_command(locale=['en'])
        original = self.target(self.post)
        self.post.title = '纸船归来'
        self.post.body = '<p>纸船返回虚构的村庄。</p>'
        self.post.cover_image = 'covers/fictional-return.png'
        self.post.save()
        self.run_command(locale=['en'], page=[self.post.pk], no_publish=True)
        target = self.target(self.post)
        self.assertTrue(target.live)
        self.assertTrue(target.has_unpublished_changes)
        self.assertEqual(target.title, original.title)
        self.assertEqual(target.body, original.body)
        self.assertEqual(target.cover_image.name, original.cover_image.name)
        self.assertEqual(target.latest_revision.content['title'], 'Translated en 纸船归来')
        self.assertIn('纸船返回虚构的村庄。', target.latest_revision.content['body'])
        self.assertEqual(target.latest_revision.content['cover_image'], 'covers/fictional-return.png')
        self.newsletter.assert_not_called()
