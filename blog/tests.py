from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.forms import modelform_factory
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from flex.models import CoverForm as FlexCoverForm, Engineer
from .models import BlogPage, CoverForm
from .tasks.tasks import generate_keywords_and_image


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class ReaderNavigationTests(TestCase):
    def setUp(self):
        from wagtail.models import Page, PageViewRestriction, Site
        from home.models import HomePage
        from .models import BlogIndexPage

        root = Page.get_first_root_node()
        self.home = root.add_child(instance=HomePage(title="Notebook", slug="notebook", banner="Field notes"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", root_page=self.home, is_default_site=True)
        self.index = self.home.add_child(instance=BlogIndexPage(title="Notes", slug="notes"))
        self.posts = [self.index.add_child(instance=BlogPage(
            title=f"Chapter {i}", slug=f"chapter-{i}", date=date(2026, 1, 1),
            body="<p>A short excerpt.</p>", cover_image="covers/example.png")) for i in range(13)]
        self.flex = self.index.add_child(instance=Engineer(
            title="Flexible chapter", slug="flexible", date=date(2026, 1, 1)))
        hidden = self.index.add_child(instance=BlogPage(
            title="Private chapter", slug="private", date=date(2026, 1, 1)))
        PageViewRestriction.objects.create(page=hidden, restriction_type="password", password="example")
        self.index.add_child(instance=BlogPage(
            title="Draft chapter", slug="draft", date=date(2026, 1, 1), live=False))

    def test_index_paginates_public_articles_twelve_at_a_time(self):
        response = self.client.get(self.index.url)
        self.assertEqual(len(response.context["posts"]), 12)
        self.assertContains(response, '?page=2')
        second = self.client.get(self.index.url, {"page": 2})
        self.assertEqual(len(second.context["posts"]), 2)
        self.assertNotContains(second, "Private chapter")
        self.assertNotContains(second, "Draft chapter")

    def test_index_invalid_and_out_of_range_pages(self):
        first = self.client.get(self.index.url, {"page": "invalid"})
        self.assertEqual(first.context["posts"].number, 1)
        last = self.client.get(self.index.url, {"page": 999})
        self.assertEqual(last.context["posts"].number, 2)

    def test_blog_chapter_links_use_titles(self):
        response = self.client.get(self.posts[1].url)
        self.assertContains(response, "← Chapter 0")
        self.assertContains(response, "Chapter 2 →")

    def test_flex_chapter_links_use_titles_and_skip_private_pages(self):
        response = self.client.get(self.flex.url)
        self.assertContains(response, "← Chapter 12")
        self.assertNotContains(response, 'rel="next"')

    def test_index_cover_is_lazy_image_with_excerpt(self):
        response = self.client.get(self.index.url)
        self.assertContains(response, 'loading="lazy"')
        self.assertContains(response, "A short excerpt.")

    def test_share_without_cover_renders_one_language_menu(self):
        response = self.client.get(self.flex.url, {"type": "share"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-language-menu', count=1)

    def test_comments_offer_wallet_help_and_localized_strings_without_bundle(self):
        response = self.client.get(self.posts[0].url)
        self.assertContains(response, 'data-wallet-help')
        self.assertContains(response, 'data-confirm=')
        self.assertNotContains(response, 'main.62b71d64.js')


class GeneratedCoverTests(TestCase):
    def assert_cover_stays_in_media(self, model, form_class, **content):
        page = model(title='Original title', date=date(2026, 1, 1), **content)
        form_type = modelform_factory(model, form=form_class, fields=['title', 'generate_cover'])
        form = form_type({'title': '../mysite/static/cover', 'generate_cover': 'on'}, instance=page)
        self.assertTrue(form.is_valid(), form.errors)
        with patch.object(generate_keywords_and_image, 'delay') as enqueue:
            page = form.save(commit=False)
        article, filename = enqueue.call_args.args
        self.assertRegex(filename, r'^covers/[0-9a-f]{32}\.png$')
        self.assertEqual(page.cover_image.name, filename)
        self.assertFalse(page.generate_cover)

        with TemporaryDirectory() as directory:
            media_root = Path(directory).resolve() / 'media'
            outside_file = Path(directory) / 'mysite/static/cover.png'
            outside_file.parent.mkdir(parents=True)
            outside_file.write_bytes(b'existing file')
            with self.settings(MEDIA_ROOT=str(media_root)):
                saved_name = generate_keywords_and_image(article, filename)
                self.assertEqual(saved_name, filename)
                destination = Path(page.cover_image.path).resolve()
                self.assertEqual(destination.parent, media_root / 'covers')
                self.assertTrue(destination.is_file())
                with Image.open(destination) as image:
                    self.assertEqual(image.format, 'PNG')
                self.assertEqual(page.cover_image.url, f'/media/{filename}')
            self.assertEqual(outside_file.read_bytes(), b'existing file')
            self.assertEqual(list(media_root.rglob('*.png')), [destination])

    def test_blog_title_cannot_escape_media(self):
        self.assert_cover_stays_in_media(
            BlogPage, CoverForm, body='<p>Translation alignment storage safety website article</p>')

    def test_flex_title_cannot_escape_media(self):
        self.assert_cover_stays_in_media(
            Engineer, FlexCoverForm,
            content=[{'type': 'full_richtext',
                      'value': '<p>Translation alignment storage safety website article</p>'}])


class NotifyOnPublishTests(TestCase):
    """F10: the newsletter goes out on publish only, once, and never for restricted pages."""

    def setUp(self):
        from wagtail.models import Page
        from blog.models import BlogPage
        self.post = Page.get_first_root_node().add_child(instance=BlogPage(
            title="Notify me", slug="notify-me", date=timezone.now().date(), body="<p>x</p>", live=False))

    def flag_and(self, publish):
        from unittest import mock
        self.post.notify_subscribers = True
        revision = self.post.save_revision()
        with mock.patch("blog.models.send_emails.delay") as delay, self.captureOnCommitCallbacks(execute=True):
            if publish:
                revision.publish()
        return delay

    def test_draft_save_sends_nothing(self):
        self.flag_and(publish=False).assert_not_called()

    def test_publish_sends_once_and_clears_flag(self):
        from unittest import mock
        self.flag_and(publish=True).assert_called_once()
        self.post.refresh_from_db()
        self.assertFalse(self.post.notify_subscribers)
        self.assertFalse(self.post.latest_revision.content["notify_subscribers"])
        with mock.patch("blog.models.send_emails.delay") as again, self.captureOnCommitCallbacks(execute=True):
            self.post.save_revision().publish()
        again.assert_not_called()

    def test_restricted_page_publish_sends_nothing(self):
        from wagtail.models import PageViewRestriction
        PageViewRestriction.objects.create(page=self.post, restriction_type="password", password="x")
        self.flag_and(publish=True).assert_not_called()

    def test_admin_form_save_with_flag_sends_nothing(self):
        """The old bug: saving the edit form (e.g. a draft) with the box ticked mailed everyone."""
        form_type = modelform_factory(BlogPage, form=CoverForm, fields=['title', 'notify_subscribers', 'generate_cover'])
        form = form_type({'title': 'Draft', 'notify_subscribers': 'on'}, instance=self.post)
        self.assertTrue(form.is_valid(), form.errors)
        with patch('blog.models.send_emails.delay') as delay:
            form.save(commit=True)
        delay.assert_not_called()
