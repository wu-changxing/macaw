from datetime import date

from django.test import TestCase, override_settings
from wagtail.contrib.search_promotions.models import Query
from wagtail.models import Locale, Page, Site

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class SearchReaderTests(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()
        self.home = root.add_child(instance=HomePage(title="Notebook", slug="notebook", banner="Field notes"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", root_page=self.home, is_default_site=True)
        english, _ = Locale.objects.get_or_create(language_code="en")
        with self.captureOnCommitCallbacks(execute=True):
            self.section = self.home.add_child(instance=BlogIndexPage(title="Notes", slug="notes"))
            for i in range(13):
                self.section.add_child(instance=BlogPage(
                    title=f"Orchard note {i}", slug=f"note-{i}", date=date(2026, 1, 1),
                    body="<p>Orchard excerpt</p>"))
            self.foreign = root.add_child(instance=BlogPage(
                title="Orchard English", slug="english", locale=english,
                date=date(2026, 1, 1), body="<p>Orchard</p>"))

    def test_search_only_returns_active_locale(self):
        chinese = self.client.get("/search/?query=Orchard")
        self.assertEqual(chinese.context["search_results"].paginator.count, 13)
        english = self.client.get("/en/search/?query=Orchard")
        self.assertEqual([p.pk for p in english.context["search_results"]], [self.foreign.pk])

    def test_anonymous_search_does_not_record_queries(self):
        self.client.get("/search/?query=Orchard")
        self.assertFalse(Query.objects.exists())

    def test_search_pagination_stays_in_locale_and_keeps_query(self):
        response = self.client.get("/search/?query=Orchard&page=2")
        results = response.context["search_results"]
        self.assertEqual((results.number, len(results)), (2, 3))
        self.assertContains(response, "query=Orchard&amp;page=1")

    def test_empty_query_has_hint_and_shared_navigation(self):
        response = self.client.get("/search/")
        self.assertContains(response, "输入关键词搜索文章")
        self.assertContains(response, 'aria-label="Primary navigation"')

