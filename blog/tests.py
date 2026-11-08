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
from .tasks.tasks import clean_tags, generate_keywords_and_image


@override_settings(
    STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
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

    def test_index_lists_all_public_posts_on_original_paper_cards(self):
        response = self.client.get(self.index.url)
        self.assertEqual(len(response.context["posts"]), 14)
        self.assertContains(response, "shadow-2xl bg-white", count=14)
        self.assertNotContains(response, '?page=2')
        self.assertNotContains(response, "Private chapter")
        self.assertNotContains(response, "Draft chapter")

    def test_index_ignores_obsolete_page_parameter(self):
        for value in (2, "invalid", 999):
            with self.subTest(page=value):
                response = self.client.get(self.index.url, {"page": value})
                self.assertEqual(len(response.context["posts"]), 14)

    def test_blog_chapter_links_keep_original_markup(self):
        from bs4 import BeautifulSoup
        response = self.client.get(self.posts[1].url)
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.select("#article-content .text-sky-600 a")
        self.assertEqual([link["href"] for link in links], [self.posts[0].url, self.posts[2].url])
        self.assertEqual([link.get_text(strip=True) for link in links], ["<", ">>>>>"])
        self.assertNotContains(response, 'aria-label="Chapter navigation"')

    def test_flex_chapter_links_keep_original_markup_and_skip_private_pages(self):
        from bs4 import BeautifulSoup
        response = self.client.get(self.flex.url)
        self.assertContains(response, f'href="{self.posts[12].url}"')
        self.assertNotContains(response, 'href="/notes/private/"')
        self.assertNotContains(response, 'rel="next"')
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertEqual([link.get_text(strip=True) for link in soup.select("#article-content .text-sky-600 a")],
                         ["<<<<<", ">"])

    def test_index_keeps_original_background_cover_and_title(self):
        response = self.client.get(self.index.url)
        self.assertContains(response, 'style="background-image: url(/media/covers/example.png)"')
        self.assertContains(response, 'glass-effect underline underline-offset-8')
        self.assertContains(response, "Chapter 0")

    def test_index_cards_load_small_lazy_covers(self):
        from bs4 import BeautifulSoup
        from .templatetags.cover_tags import CARD_WIDTH, MADE_PER_RENDER
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            (Path(media) / "covers").mkdir()
            Image.new("RGB", (1920, 1186), "white").save(Path(media) / "covers/example.png")
            self.client.get(self.index.url)  # first render makes the one shared copy
            soup = BeautifulSoup(self.client.get(self.index.url).content, "html.parser")
            card = f"/media/cards/covers/example-{CARD_WIDTH}.webp"
            covers = soup.select("div.h-96.bg-contain")
            self.assertEqual(covers[0]["style"], f"background-image: url({card})")
            self.assertEqual({c.get("data-cover") for c in covers[1:13]}, {card})
            self.assertFalse(any(c.get("style") for c in covers[1:]))
            with Image.open(Path(media) / card.removeprefix("/media/")) as image:
                self.assertEqual((image.format, image.width), ("WEBP", CARD_WIDTH))
            self.assertGreater(MADE_PER_RENDER, 0)

    def test_index_makes_a_few_cover_copies_per_render(self):
        from .templatetags.cover_tags import MADE_PER_RENDER
        with TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            (Path(media) / "covers").mkdir()
            for i, post in enumerate(self.posts):
                Image.new("RGB", (1920, 1186), "white").save(Path(media) / f"covers/{i}.png")
                post.cover_image = f"covers/{i}.png"
                post.save()
            response = self.client.get(self.index.url)
            self.assertEqual(len(list((Path(media) / "cards/covers").iterdir())), MADE_PER_RENDER)
            self.assertContains(response, "/media/covers/12.png")  # not made yet: full-size, as before

    def test_arabic_pages_are_right_to_left(self):
        from wagtail.models import Locale
        arabic = Locale.objects.create(language_code="ar")
        self.home.copy_for_translation(arabic)
        self.index.copy_for_translation(arabic)
        post = self.posts[0].copy_for_translation(arabic)
        post.live = True
        post.save()
        self.assertContains(self.client.get(post.url), '<html lang="ar" dir="rtl">')
        self.assertContains(self.client.get(self.posts[0].url), '<html lang="zh-hans" dir="ltr">')

    def test_wallet_bundle_mounts_only_the_wallet(self):
        import re
        from django.conf import settings
        from django.template.loader import render_to_string
        script = re.search(r'src="/static/(js/main\.\w+\.js)"', render_to_string("wallet.html")).group(1)
        bundle = (Path(settings.BASE_DIR) / "mysite/static" / script).read_text()
        self.assertEqual(re.findall(r'getElementById\("([\w-]+)"\)', bundle), ["wallet"])

    def test_share_without_cover_renders_one_language_menu(self):
        response = self.client.get(self.flex.url, {"type": "share"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="language-switch-button"', count=1)
        self.assertContains(response, 'id="language-switch-dropdown"', count=1)

    def test_comments_restore_original_form_and_wallet_bundle(self):
        response = self.client.get(self.posts[0].url)
        self.assertContains(response, 'data-comment-form')
        self.assertContains(response, '用钱包签名并发布 · Sign &amp; post')
        self.assertContains(response, 'main.41a419b1.js')
        self.assertContains(response, 'id="wallet"')

    def test_language_links_and_wallet_share_one_top_bar(self):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(self.client.get(self.posts[0].url).content, "html.parser")
        bars = soup.select(".reader-topbar")
        self.assertEqual(len(bars), 1)
        self.assertIsNotNone(bars[0].select_one(".topbar-langs"))
        self.assertIsNotNone(bars[0].select_one("#language-switch-button"))
        self.assertIsNotNone(bars[0].select_one("#wallet"))


class GeneratedCoverTests(TestCase):
    def test_html_entities_do_not_become_keywords(self):
        cleaned = clean_tags('<p>Rust &amp; Haskell&nbsp;compilers &lt;3</p>')
        self.assertNotIn('amp', cleaned)
        self.assertNotIn('nbsp', cleaned)
        self.assertNotIn('lt', cleaned.split())

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
