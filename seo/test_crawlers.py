"""Crawler exports must contain only published, public, genuinely translated data."""
import json
from datetime import date, datetime, timedelta
from xml.etree import ElementTree

from django.core.cache import cache
from wagtail.models import Locale, PageViewRestriction

from blog.models import BlogIndexPage, BlogPage
from flex.models import Engineer
from seo.test_metadata import PageFixture


class CrawlerTests(PageFixture):
    def test_llms_groups_live_sections_and_real_english(self):
        self.home.search_description = "A fictional garden notebook."
        self.home.save()
        self.post.search_description = "Apple notes\nfrom the orchard."
        self.post.save()
        self.home.add_child(instance=BlogIndexPage(title="Empty section", slug="empty"))
        hidden = self.home.add_child(instance=BlogIndexPage(title="Private section", slug="private"))
        PageViewRestriction.objects.create(page=hidden, restriction_type="password", password="fictional")
        self.index.add_child(instance=BlogPage(title="Draft fruit", slug="draft", date=date(2026, 1, 1), live=False))
        english = Locale.objects.create(language_code="en")
        for page in (self.home, self.index):
            page.copy_for_translation(english)
        translated = self.post.copy_for_translation(english)
        translated.live = True
        translated.save()
        text = self.client.get("/llms.txt").content.decode()
        self.assertTrue(text.startswith("# 吴长星的博客\n"))
        self.assertIn("A fictional garden notebook.", text)
        self.assertIn("## Orchard\n", text)
        self.assertIn("## Empty section\n", text)
        self.assertIn(f"- [{self.post.title}](https://testserver/orchard/apples/): Apple notes from the orchard.", text)
        self.assertIn("https://testserver/llms-full.txt", text)
        self.assertNotIn("## English", text)
        self.assertNotIn("Draft fruit", text)
        self.assertNotIn("Private section", text)
        translated.title = "Fictional apple notes"
        translated.save()
        cache.clear()
        text = self.client.get("/llms.txt").content.decode()
        self.assertIn("## English\n", text)
        self.assertIn("[Fictional apple notes](https://testserver/en/orchard/apples/)", text)
        self.assertEqual(text.count(f"[{self.post.title}]"), 1)
        # One-hour response cache covers both exports.
        for path in ("/llms.txt", "/llms-full.txt"):
            self.assertIn("max-age=3600", self.client.get(path)["Cache-Control"])

    def test_full_export_plain_body_boundaries_entities_and_privacy(self):
        self.post.body = "<p>Apples &amp; pears.</p><p>Another paragraph.</p>"
        self.post.save()
        self.index.add_child(instance=Engineer(title="Fictional stream", slug="stream", date=date(2026, 2, 3),
            content=[("full_richtext", "<p>Stream &amp; text.</p>"), ("math", "x+y")]))
        self.index.add_child(instance=BlogPage(title="Unpublished", slug="unpublished", date=date(2026, 1, 1), live=False))
        restricted = self.index.add_child(instance=BlogPage(title="Restricted fruit", slug="secret", date=date(2026, 1, 1)))
        PageViewRestriction.objects.create(page=restricted, restriction_type="password", password="fictional")
        response = self.client.get("/llms-full.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        text = response.content.decode()
        self.assertIn("https://testserver/orchard/apples/", text)
        self.assertIn("2026-01-02", text)
        self.assertIn("Apples & pears.\nAnother paragraph.", text)
        self.assertIn("Stream & text.", text)
        self.assertIn("x+y", text)
        self.assertIn("\n---\n", text)
        self.assertNotIn("<p>", text)
        self.assertNotIn("Unpublished", text)
        self.assertNotIn("Restricted fruit", text)
        self.post.title = "Changed after cache"
        self.post.save()
        self.assertNotIn("Changed after cache", self.client.get("/llms-full.txt").content.decode())

    def test_sitemap_published_lastmod_and_cover_namespace(self):
        # Saving a draft revision timestamp must not make the live article look newer.
        self.post.latest_revision_created_at = self.modified + timedelta(days=2)
        self.post.save()
        root = ElementTree.fromstring(self.client.get("/sitemap.xml").content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "i": "http://www.google.com/schemas/sitemap-image/1.1"}
        urls = root.findall("s:url", ns)
        post = next(node for node in urls if node.find("s:loc", ns).text.endswith("/apples/"))
        self.assertEqual(post.find("s:loc", ns).text, "https://testserver/orchard/apples/")
        self.assertEqual(datetime.fromisoformat(post.find("s:lastmod", ns).text), self.modified)
        self.assertEqual(post.find("i:image/i:loc", ns).text, "https://testserver/media/covers/fictional.png")
        self.assertFalse(next(node for node in urls if node.find("s:loc", ns).text.endswith("/orchard/")).findall("i:image", ns))

    def test_nested_and_unsectioned_posts_are_discoverable(self):
        nested = self.post.add_child(instance=Engineer(title="Nested fruit note", slug="nested", date=date(2026, 1, 2)))
        direct = self.home.add_child(instance=BlogPage(title="Unsectioned fruit note", slug="direct", date=date(2026, 1, 2)))
        text = self.client.get("/llms.txt").content.decode()
        self.assertIn("[Nested fruit note](https://testserver/orchard/apples/nested/)", text)
        self.assertIn("[Unsectioned fruit note](https://testserver/direct/)", text)
        self.assertEqual(text.count("## Orchard"), 1)
        self.assertIn("## Posts", text)
        article, crumbs = [json.loads(node.string) for node in self.soup(nested).find_all("script", type="application/ld+json")]
        self.assertEqual(article["articleSection"], "Orchard")
        self.assertEqual([node["name"] for node in crumbs["itemListElement"]],
                         [self.home.title, self.index.title, nested.title])

    def test_english_requires_a_public_default_locale_source(self):
        english = Locale.objects.create(language_code="en")
        en_home = self.home.copy_for_translation(english)
        en_home.live = True
        en_home.save()
        en_home.add_child(instance=BlogPage(title="English original without source", slug="english-only",
                                         date=date(2026, 1, 2), locale=english))
        self.assertNotIn("English original without source", self.client.get("/llms.txt").content.decode())

    def test_llms_preserves_search_description_and_bounds_body_fallback(self):
        description = "A fictional description. " * 8
        self.post.search_description = description.strip()
        self.post.save()
        text = self.client.get("/llms.txt").content.decode()
        self.assertIn(": " + description.strip(), text)
        self.post.search_description = ""
        self.post.body = "<p>" + "果" * 150 + "</p>"
        self.post.save()
        cache.clear()
        text = self.client.get("/llms.txt").content.decode()
        self.assertIn(": " + "果" * 120 + "\n", text)
        self.assertNotIn("果" * 121, text)
