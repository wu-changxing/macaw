from datetime import date

from django.test import TestCase, override_settings
from wagtail.contrib.search_promotions.models import Query
from wagtail.models import Locale, Page, Site

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
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

    def test_empty_query_has_original_search_form(self):
        response = self.client.get("/search/")
        self.assertContains(response, '>Search</h1>')
        self.assertContains(response, 'name="query"')
        self.assertContains(response, 'value="Search" class="button"')


    def test_search_results_sit_on_the_paper_sheet(self):
        response = self.client.get("/search/?query=Orchard")
        self.assertContains(response, "css/paper-polish.css")
        self.assertContains(response, 'class="search-sheet shadow-2xl bg-white')
        self.assertContains(response, '<ul class="search-results">')

    def test_reader_pages_load_the_polish_stylesheet(self):
        self.assertContains(self.client.get("/notes/"), "css/paper-polish.css")
        self.assertContains(self.client.get("/notes/note-0/"), "css/paper-polish.css")
