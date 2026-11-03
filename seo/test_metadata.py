"""Rendered metadata contracts for fictional articles and translations."""
import json
from datetime import date, datetime, timezone as dt_timezone

from bs4 import BeautifulSoup
from django.core.cache import cache
from django.test import TestCase, override_settings
from wagtail.models import Locale, Page, Site

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class PageFixture(TestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        root = Page.get_first_root_node()
        self.home = root.add_child(instance=HomePage(title="Fictional garden", slug="garden", banner="Garden notes"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", port=80, root_page=self.home, is_default_site=True)
        self.index = self.home.add_child(instance=BlogIndexPage(title="Orchard", slug="orchard"))
        # Fixed near midnight UTC: the site timezone falls on the preceding date.
        self.modified = datetime(2026, 11, 3, 0, 30, tzinfo=dt_timezone.utc)
        self.post = self.index.add_child(instance=BlogPage(
            title="Apple </script> notes", slug="apples", date=date(2026, 1, 2),
            body="<p>苹果树 grows well.</p>", cover_image="covers/fictional.png",
            last_published_at=self.modified))

    def soup(self, page):
        return BeautifulSoup(self.client.get(page.url).content, "html.parser")


class MetadataTests(PageFixture):
    def test_article_structured_data_and_breadcrumbs(self):
        soup = self.soup(self.post)
        scripts = soup.find_all("script", type="application/ld+json")
        article = json.loads(scripts[0].string)
        self.assertEqual(article["mainEntityOfPage"], "https://testserver/orchard/apples/")
        self.assertEqual(article["inLanguage"], "zh-hans")
        self.assertEqual(article["dateModified"], self.modified.isoformat())
        self.assertEqual(article["publisher"], article["author"])
        self.assertEqual(article["author"]["url"], "https://aaron404.com/")
        self.assertEqual(article["author"]["sameAs"], ["https://github.com/wu-changxing"])
        self.assertEqual(article["wordCount"], 5)  # Three CJK characters + two Latin words.
        self.assertEqual(article["articleSection"], "Orchard")
        self.assertEqual(article["image"], "https://testserver/media/covers/fictional.png")
        self.assertIn(r"<\/script>", scripts[0].string)
        crumbs = json.loads(scripts[1].string)
        self.assertEqual(crumbs["@type"], "BreadcrumbList")
        self.assertEqual([x["name"] for x in crumbs["itemListElement"]],
                         ["Fictional garden", "Orchard", self.post.title])
        self.assertEqual([x["position"] for x in crumbs["itemListElement"]], [1, 2, 3])
        self.assertTrue(all(x["item"].startswith("https://") for x in crumbs["itemListElement"]))

    def test_home_identity_language_and_search(self):
        graph = json.loads(self.soup(self.home).find("script", type="application/ld+json").string)["@graph"]
        self.assertEqual(graph[0]["inLanguage"], "zh-hans")
        self.assertEqual(graph[0]["potentialAction"], {
            "@type": "SearchAction", "target": "https://aaron404.com/search/?query={search_term_string}",
            "query-input": "required name=search_term_string"})
        self.assertEqual(graph[1]["sameAs"], ["https://github.com/wu-changxing"])

    def test_social_metadata_and_real_translation_locales(self):
        french = Locale.objects.create(language_code="fr")
        self.home.copy_for_translation(french)
        self.index.copy_for_translation(french)
        translated = self.post.copy_for_translation(french)
        translated.live = True
        translated.save()
        self.assertFalse(self.soup(self.post).find_all("meta", property="og:locale:alternate"))
        translated.title = "Pommes imaginaires"
        translated.save()
        soup = self.soup(self.post)
        self.assertEqual(soup.find("meta", property="og:locale")["content"], "zh_CN")
        self.assertEqual([x["content"] for x in soup.find_all("meta", property="og:locale:alternate")], ["fr_FR"])
        self.assertEqual(soup.find("meta", property="og:site_name")["content"], "吴长星的博客")
        self.assertEqual(soup.find("meta", property="article:published_time")["content"], "2026-01-02")
        self.assertEqual(datetime.fromisoformat(soup.find("meta", property="article:modified_time")["content"]), self.modified)
        self.assertEqual(soup.find("meta", property="article:author")["content"], "https://aaron404.com/")
        self.assertEqual(soup.find("meta", attrs={"name": "twitter:card"})["content"], "summary_large_image")
        for node in soup.select('link[rel="canonical"], link[hreflang], link[type="application/rss+xml"]'):
            self.assertTrue(node["href"].startswith("https://"), node)
        self.post.cover_image = ""
        self.post.save()
        soup = self.soup(self.post)
        self.assertEqual(soup.find("meta", attrs={"name": "twitter:card"})["content"], "summary")
        self.assertNotIn("image", json.loads(soup.find("script", type="application/ld+json").string))
