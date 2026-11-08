"""Backend contracts from the live audit; all content is fictional."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase
from PIL import Image
from wagtail.models import Locale

from seo.test_metadata import PageFixture
from seo.templatetags.seo_tags import https_url, untranslated_source


class SocialCardTests(PageFixture):
    def setUp(self):
        super().setUp()
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        override = self.settings(MEDIA_ROOT=directory.name)
        override.enable()
        self.addCleanup(override.disable)

    def test_cover_becomes_cached_jpeg_and_changes_with_source(self):
        path = Path(settings.MEDIA_ROOT, self.post.cover_image.name)
        path.parent.mkdir(parents=True)
        Image.new("RGB", (1792, 1024), "red").save(path)
        soup = self.soup(self.post)
        url = soup.find("meta", property="og:image")["content"]
        self.assertRegex(url, r"https://testserver/media/og/[a-f0-9]+\.jpg$")
        rendition = Path(settings.MEDIA_ROOT, urlsplit(url).path.removeprefix("/media/"))
        with Image.open(rendition) as image:
            self.assertEqual((image.size, image.format), ((1200, 630), "JPEG"))
        stamp = rendition.stat().st_mtime_ns
        self.assertEqual(self.soup(self.post).find("meta", property="og:image")["content"], url)
        self.assertEqual(rendition.stat().st_mtime_ns, stamp)
        self.assertEqual(soup.find("meta", attrs={"name": "twitter:image"})["content"], url)
        Image.new("RGB", (1800, 1000), "blue").save(path)
        self.assertNotEqual(self.soup(self.post).find("meta", property="og:image")["content"], url)

    def test_missing_cover_home_and_index_use_real_default(self):
        with Image.open("mysite/static/og-default.jpg") as image:
            self.assertEqual((image.size, image.format), ((1200, 630), "JPEG"))
        for page in (self.post, self.home, self.index):
            with self.subTest(page=page.title):
                soup = self.soup(page)
                self.assertEqual(soup.find("meta", property="og:image")["content"],
                                 "https://testserver/static/og-default.jpg")
                self.assertEqual(soup.find("meta", attrs={"name": "twitter:card"})["content"], "summary_large_image")
        data = json.loads(self.soup(self.index).find("script", type="application/ld+json").string)
        self.assertEqual((data["@type"], data["url"]), ("CollectionPage", https_url(self.index.full_url)))

    def test_missing_default_and_cover_do_not_advertise_image(self):
        with patch("seo.templatetags.seo_tags.finders.find", return_value=None):
            soup = self.soup(self.post)
        self.assertIsNone(soup.find("meta", property="og:image"))
        self.assertEqual(soup.find("meta", attrs={"name": "twitter:card"})["content"], "summary")


class ReaderAuditTests(PageFixture):
    def test_touch_icons_resolve_to_existing_180_pixel_icon(self):
        for path in ("/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response["Location"], "/static/apple-touch-icon.png")
        with Image.open("mysite/static/apple-touch-icon.png") as image:
            self.assertEqual(image.size, (180, 180))

    def test_footer_email_attributes_on_both_reader_types(self):
        for page in (self.post, self.index):
            soup = self.soup(page)
            field = soup.select_one('footer input[name="email"]')
            self.assertEqual(field["type"], "email")
            self.assertIn("required", field.attrs)
            self.assertEqual(field["aria-label"], "Email address")
            self.assertEqual(field["id"], "footer-subscribe-email")
            self.assertIsNone(soup.find(id="exampleFormControlInput1"))

    def test_subscription_validation_language_matches_document(self):
        for language in ("en", "zh-hans"):
            path = "/en/subscribe/new/" if language == "en" else "/subscribe/new/"
            soup = BeautifulSoup(self.client.post(path, {"email": "invalid"}).content, "html.parser")
            self.assertEqual(soup.html["lang"], language)
            if language == "en":
                self.assertIn("Enter a valid email address.", soup.get_text())

    def test_search_uses_active_language(self):
        for path, language in (("/search/", "zh-hans"), ("/en/search/", "en"), ("/ja/search/", "ja")):
            self.assertContains(self.client.get(path), f'<html lang="{language}">')

    def test_not_found_svg_has_no_artboard_tooltip(self):
        soup = BeautifulSoup(self.client.get("/not-a-real-page/").content, "html.parser")
        self.assertFalse(soup.select("svg title"))

    def test_home_lastmod_uses_newest_live_descendant_or_home(self):
        self.home.last_published_at = self.modified - timedelta(days=10)
        self.home.save()
        self.index.add_child(instance=type(self.post)(title="Draft", slug="draft", date=self.post.date,
            live=False, last_published_at=self.modified + timedelta(days=20)))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for expected in (self.modified, self.modified + timedelta(days=1)):
            cache.clear()
            root = ET.fromstring(self.client.get("/sitemap.xml").content)
            node = next(n for n in root if n.find("s:loc", ns).text == https_url(self.home.full_url))
            self.assertEqual(datetime.fromisoformat(node.find("s:lastmod", ns).text), expected)
            self.home.last_published_at = self.modified + timedelta(days=1)
            self.home.save()


class DiscoveryCacheTests(PageFixture):
    paths = ("/llms.txt", "/llms-full.txt", "/sitemap.xml", "/robots.txt", "/feed/")

    def test_crawler_headers_and_cached_bodies(self):
        for path in self.paths:
            with self.subTest(path=path):
                first = self.client.get(path)
                self.assertEqual(first["Cache-Control"], "public, max-age=3600, s-maxage=3600")
                with self.assertNumQueries(0):
                    second = self.client.get(path)
                self.assertEqual(first.content, second.content)

    def test_publish_and_unpublish_invalidate_all_exports(self):
        for path in self.paths:
            self.client.get(path)
        self.post.title = "Newly published fruit"
        with self.captureOnCommitCallbacks(execute=True):
            self.post.save_revision().publish()
        for path in self.paths:
            with self.subTest(path=path), patch("seo.views.https_url", wraps=https_url) as build_url:
                response = self.client.get(path)
                self.assertTrue(build_url.called, f"{path} must regenerate after publishing")
                if path in ("/llms.txt", "/llms-full.txt", "/feed/"):
                    self.assertIn("Newly published fruit", response.content.decode())
        with self.captureOnCommitCallbacks(execute=True):
            self.post.unpublish()
        for path in ("/llms.txt", "/llms-full.txt", "/feed/", "/sitemap.xml"):
            self.assertNotIn("/orchard/apples/", self.client.get(path).content.decode())
        with patch("seo.views.https_url", wraps=https_url) as build_url:
            self.client.get("/robots.txt")
            self.assertTrue(build_url.called)

    def test_reader_html_is_not_publicly_cached(self):
        response = self.client.get(self.post.url)
        self.assertNotIn("public", response.get("Cache-Control", ""))
        self.assertIn("csrfmiddlewaretoken", response.content.decode())


class LocalizedFeedTests(PageFixture):
    def test_default_locale_also_has_an_explicit_feed_path(self):
        response = self.client.get(f"/{settings.LANGUAGE_CODE}/feed/")
        self.assertEqual(response.status_code, 200)
        feed = ET.fromstring(response.content)
        self.assertEqual(feed.find(".//channel/language").text, settings.LANGUAGE_CODE)
        self.assertEqual([n.text for n in feed.findall(".//item/title")], [self.post.title])

    def test_each_locale_feed_and_head_alternate_exclude_untranslated(self):
        for code, _ in settings.WAGTAIL_CONTENT_LANGUAGES:
            locale, _ = Locale.objects.get_or_create(language_code=code)
            if code == settings.LANGUAGE_CODE:
                continue
            home = self.home.copy_for_translation(locale)
            home.live = True
            home.save()
            self.index.copy_for_translation(locale)
            copy = self.post.copy_for_translation(locale)
            copy.live = True
            copy.save()
            path = f"/{code}/feed/"
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(ET.fromstring(response.content).findall(".//item"))
            copy.title = "Translated orchard"
            copy.save()
            cache.clear()
            feed = ET.fromstring(self.client.get(path).content)
            self.assertEqual([n.text for n in feed.findall(".//item/title")], [copy.title])
            self.assertEqual(feed.find(".//channel/language").text, code)
            self.assertEqual(self.soup(copy).find("link", type="application/rss+xml")["href"],
                             f"https://testserver{path}")


class UntranslatedPredicateTests(SimpleTestCase):
    def test_title_predicate_boundaries_and_cjk_locales(self):
        from seo.templatetags.seo_tags import is_untranslated_title
        for code in ("en", "fr", "ar", "ru"):
            self.assertTrue(is_untranslated_title("旧中文标题", "新中文标题", code))
            self.assertTrue(is_untranslated_title("一二三四abcdef", "Source", code))
            self.assertFalse(is_untranslated_title("一二三abcdefg", "Source", code))
            self.assertFalse(is_untranslated_title("", "Source", code))
        for code in ("ja", "ko", "zh-hant"):
            self.assertFalse(is_untranslated_title("旧中文标题", "新中文标题", code))
            self.assertTrue(is_untranslated_title("相同", "相同", code))


class FeedBatchTests(SimpleTestCase):
    def test_feed_stops_after_thirty_eligible_posts(self):
        from seo.views import PostsFeed

        def articles(**kwargs):
            yield "untranslated"
            yield from range(30)
            self.fail("Feed read past its thirtieth eligible post")

        queryset = MagicMock()
        queryset.__iter__.side_effect = articles
        queryset.iterator.side_effect = articles
        with patch("seo.views.posts", return_value=queryset), patch(
            "seo.views.untranslated_source", side_effect=lambda page: page == "untranslated"
        ):
            self.assertEqual(PostsFeed().items("en"), list(range(30)))
        queryset.iterator.assert_called_once_with(chunk_size=30)


class RetitledCopyTests(PageFixture):
    def test_retitled_chinese_copy_uses_shared_exclusion_rule(self):
        locale = Locale.objects.create(language_code="en")
        for page in (self.home, self.index):
            copy = page.copy_for_translation(locale)
            copy.live = True
            copy.save()
        copy = self.post.copy_for_translation(locale)
        copy.title = "旧的中文标题"
        copy.live = True
        copy.save()
        self.assertEqual(untranslated_source(copy).pk, self.post.pk)
        self.assertContains(self.client.get(copy.url), 'content="noindex,follow"')
        for path in ("/sitemap.xml", "/llms.txt", "/en/feed/"):
            self.assertNotIn(https_url(copy.full_url), self.client.get(path).content.decode())
