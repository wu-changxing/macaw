from importlib import import_module
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, override_settings
from wagtail.models import Page, Revision

from .models import HomePage


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class RetiredPageTests(TestCase):
    def test_cleanup_restores_parent_explorer_and_preserves_tree(self):
        parent = Page.get_first_root_node().add_child(instance=HomePage(
            title="Morgan's notebook", slug="morgan-notebook", banner="Field notes"))
        retired = parent.add_child(instance=Page(title="Retired", slug="retired", live=False))
        child = retired.add_child(instance=Page(title="Retired child", slug="retired-child", live=False))
        alias = parent.add_child(instance=Page(
            title="Retired alias", slug="retired-alias", live=False, alias_of=child))
        survivor = parent.add_child(instance=Page(title="Notes", slug="notes"))
        revision = child.save_revision()
        content_type = ContentType.objects.create(app_label="feed", model="feedpage")
        Page.objects.filter(pk__in=[retired.pk, child.pk]).update(content_type=content_type)
        self.assertIsNone(content_type.model_class())
        user = get_user_model().objects.create_superuser("morgan", "morgan@example.com", "fictional-password")
        self.client.force_login(user)

        migration = import_module("home.migrations.0002_remove_retired_pages")
        historical_apps = MigrationExecutor(connection).loader.project_state().apps
        migration.remove_retired_pages(historical_apps, SimpleNamespace(connection=connection))

        self.assertFalse(Page.objects.filter(pk__in=[retired.pk, child.pk, alias.pk]).exists())
        self.assertFalse(Revision.objects.filter(pk=revision.pk).exists())
        self.assertFalse(ContentType.objects.filter(pk=content_type.pk).exists())
        parent.refresh_from_db()
        self.assertEqual(parent.numchild, 1)
        self.assertEqual(parent.get_children().get().pk, survivor.pk)
        self.assertEqual(Page.find_problems(), ([], [], [], [], []))
        self.assertEqual(self.client.get(f"/admin/pages/{parent.pk}/").status_code, 200)

    def test_stale_content_types_are_removed_only_when_unreferenced(self):
        from django.contrib.auth.models import Permission

        used = ContentType.objects.create(app_label="echo_atrium", model="retiredentry")
        unused = ContentType.objects.create(app_label="word_quiz", model="retiredword")
        permission = Permission.objects.create(
            content_type=used, codename="view_retiredentry", name="View retired entry")
        migration = import_module("home.migrations.0002_remove_retired_pages")
        historical_apps = MigrationExecutor(connection).loader.project_state().apps
        migration.remove_retired_pages(historical_apps, SimpleNamespace(connection=connection))

        self.assertTrue(ContentType.objects.filter(pk=used.pk).exists())
        self.assertTrue(Permission.objects.filter(pk=permission.pk).exists())
        self.assertFalse(ContentType.objects.filter(pk=unused.pk).exists())


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class BladeHomeTests(TestCase):
    """The home page poster: name, doors, section credits and language links, built from fictional pages."""

    def setUp(self):
        from bs4 import BeautifulSoup
        from django.core.cache import cache
        from wagtail.models import Locale, Site

        from blog.models import BlogIndexPage
        from .models import HomeItem, HomeItemOrderable

        cache.clear()
        self.addCleanup(cache.clear)
        self.soup = lambda url: BeautifulSoup(self.client.get(url).content, "html.parser")
        self.home = Page.get_first_root_node().add_child(instance=HomePage(
            title="Notebook", slug="notebook", banner="Banner that must stay hidden"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", port=80, root_page=self.home, is_default_site=True)
        self.scifi = self.home.add_child(instance=BlogIndexPage(title="sci-fi", slug="blog"))
        self.musings = self.home.add_child(instance=BlogIndexPage(title="Musings", slug="musings"))
        self.novels = self.home.add_child(instance=BlogIndexPage(title="Novels", slug="novels"))
        # SECTION_MIN_PAGES is 20: sci-fi sits exactly on it, musings above, novels one short
        for section, count in ((self.scifi, 20), (self.musings, 22), (self.novels, 19)):
            for i in range(count):
                section.add_child(instance=Page(title=f"Post {i}", slug=f"post-{i}"))
        english = Locale.objects.create(language_code="en")
        self.home_en = self.publish(self.home.copy_for_translation(english))
        self.musings_en = self.musings.copy_for_translation(english)
        self.musings_en.title = "Here is the translation: Musings"
        self.musings_en = self.publish(self.musings_en)
        self.doors = {}
        for name, link in (("Musings", "https://example.com/musings/"), ("Archived", "http://archive.example.com"),
                           ("Bilibili", "https://video.example.com/whisper/"), ("Scratch", "http://scratch.example.com")):
            self.doors[name] = HomeItem.objects.create(name=name, link=link, intro=name)
            HomeItemOrderable.objects.create(page=self.home, item=self.doors[name])

    def publish(self, page):
        page.save_revision().publish()
        page.refresh_from_db()
        return page

    def test_home_renders_name_without_banner(self):
        response = self.client.get(self.home.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("吴长星", html)
        self.assertEqual(self.soup(self.home.url).find("h1").get_text(strip=True)[:3], "吴长星")
        self.assertNotIn("Banner that must stay hidden", html)

    def test_doors_link_out_with_new_tab_for_external_sites(self):
        soup = self.soup(self.home.url)
        for name in ("Archived", "Bilibili", "Scratch"):
            with self.subTest(door=name):
                links = soup.find_all("a", href=self.doors[name].link)
                self.assertTrue(links)
                for link in links:
                    self.assertEqual(link.get("target"), "_blank")
                    self.assertIn("noopener", link.get("rel"))
        self.assertTrue(soup.select(f'a.d-blade[href="{self.musings.url}"]'))
        self.assertTrue(soup.select(f'a.d-shadow[href="{self.scifi.url}"]'))

    def test_sections_use_source_labels_and_localized_links(self):
        soup = self.soup(self.home_en.url)
        links = [(a.select_one(".t").get_text(strip=True), a["href"]) for a in soup.select("nav.blade-sections a")]
        self.assertEqual(links, [("sci-fi", self.scifi.url), ("Musings", self.musings_en.url)])
        self.assertNotIn("Here is the translation", soup.body.decode())  # the SEO head may still name it
        self.assertTrue(soup.select(f'a.d-blade[href="{self.musings_en.url}"]'))

    def test_thin_sections_stay_off_the_home_page(self):
        from .models import SECTION_MIN_PAGES

        self.assertEqual(SECTION_MIN_PAGES, 20)
        labels = lambda: [a.select_one(".t").get_text(strip=True) for a in self.soup(self.home.url).select("nav.blade-sections a")]
        self.assertIn("sci-fi", labels())       # exactly 20 live pages
        self.assertNotIn("Novels", labels())    # 19 live pages
        self.scifi.get_children().first().unpublish()   # 19 left: drops off
        self.musings.get_children().first().unpublish()  # 21 left: still shown
        self.assertEqual(labels(), ["Musings"])

    def test_credit_names_the_two_doors_in_chinese(self):
        names = [a.select_one(".zh").get_text(strip=True) for a in self.soup(self.home.url).select("nav.blade-sections a")]
        self.assertEqual(names, ["回潮", "多余的沉思"])

    def test_language_links_point_to_live_translations(self):
        soup = self.soup(self.home_en.url)
        links = {a["hreflang"]: a for a in soup.select("nav.blade-lang a")}
        self.assertEqual(links["zh-hans"]["href"], self.home.url)
        self.assertEqual(links["en"]["href"], self.home_en.url)
        self.assertEqual(links["en"].get("aria-current"), "page")
        self.assertNotIn("ja", links)
