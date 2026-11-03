from django.test import TestCase, override_settings
from django.utils import timezone
from wagtail.models import Page, Site

from blog.models import BlogPage


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class SeoEndpointTests(TestCase):
    def setUp(self):
        root = Page.get_first_root_node()
        self.post = root.add_child(instance=BlogPage(
            title="关于博客", slug="about-blog", date=timezone.now().date(),
            body="<p>这是一篇关于博客迁移的文章。</p>"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", port=80, root_page=root, is_default_site=True)

    def test_robots_points_to_sitemap_and_hides_admin(self):
        text = self.client.get("/robots.txt").content.decode()
        self.assertIn("Sitemap: http://testserver/sitemap.xml", text)
        self.assertIn("Disallow: /admin/", text)

    def test_sitemap_lists_post(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/about-blog/", response.content.decode())

    def test_feed_and_llms_list_post(self):
        self.assertIn("关于博客", self.client.get("/feed/").content.decode())
        llms = self.client.get("/llms.txt").content.decode()
        self.assertIn("[关于博客](", llms)
        self.assertIn("这是一篇关于博客迁移的文章", llms)

    def test_article_head_has_seo_tags_and_comments(self):
        html = self.client.get(self.post.url).content.decode()
        self.assertIn('<html lang="zh-hans">', html)
        self.assertIn('<meta name="description" content="这是一篇关于博客迁移的文章。">', html)
        self.assertIn('rel="canonical"', html)
        self.assertIn('"@type": "BlogPosting"', html)
        self.assertIn('id="wallet-comments"', html)

    def test_favicon_redirects_to_static(self):
        self.assertEqual(self.client.get("/favicon.ico")["Location"], "/static/favicon.ico")


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class PrivacyTests(TestCase):
    """Drafts and restricted pages must not leak through API, search or share mode."""

    def setUp(self):
        from blog.models import BlogIndexPage
        from wagtail.models import PageViewRestriction
        root = Page.get_first_root_node()
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", port=80, root_page=root, is_default_site=True)
        # Wagtail 6+ updates the search index on commit; run those callbacks inside TestCase.
        with self.captureOnCommitCallbacks(execute=True):
            self.index = root.add_child(instance=BlogIndexPage(title="Musings", slug="musings"))
            day = timezone.now().date()
            self.public = self.index.add_child(instance=BlogPage(title="Open post", slug="open", date=day, body="<p>uniqueword</p>"))
            self.draft = self.index.add_child(instance=BlogPage(title="Draft post", slug="draft", date=day, body="<p>x</p>", live=False))
            self.secret = self.index.add_child(instance=BlogPage(title="Secret post", slug="secret", date=day, body="<p>uniqueword</p>"))
        PageViewRestriction.objects.create(page=self.secret, restriction_type="password", password="x")

    def test_api_children_only_public_live(self):
        data = self.client.get(f"/api/v2/pages/{self.index.id}/").json()
        self.assertEqual([c["title"] for c in data["children"]], ["Open post"])
        child = data["children"][0]
        self.assertEqual(set(child["meta"]), {"type", "html_url", "detail_url"})
        self.assertEqual(child["meta"]["type"], "blogpage")
        self.assertNotIn("html_url", child)

    def test_asset_listing_endpoints_removed(self):
        self.assertEqual(self.client.get("/api/v2/images/").status_code, 404)
        self.assertEqual(self.client.get("/api/v2/documents/").status_code, 404)

    def test_search_hides_restricted_pages(self):
        html = self.client.get("/search/?query=uniqueword").content.decode()
        self.assertIn("Open post", html)
        self.assertNotIn("Secret post", html)

    def test_tracking_params_keep_normal_template(self):
        html = self.client.get(self.public.url + "?utm_source=email").content.decode()
        self.assertIn('id="wallet-comments"', html)


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
              "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class LocaleSeoTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.addCleanup(cache.clear)
        from home.models import HomePage
        from wagtail.models import Locale
        root = Page.get_first_root_node()
        self.home = root.add_child(instance=HomePage(title="Home", slug="home-seo", banner="Welcome"))
        Site.objects.all().delete()
        Site.objects.create(hostname="testserver", port=80, root_page=self.home, is_default_site=True)
        self.french = Locale.objects.create(language_code="fr")
        self.fr_home = self.home.copy_for_translation(self.french)
        self.fr_home.live = True
        self.fr_home.save()
        self.post = self.home.add_child(instance=BlogPage(
            title="中文原文", slug="source", date=timezone.now().date(), body="<p>中文内容</p>"))
        self.copy = self.post.copy_for_translation(self.french)
        self.copy.live = True
        self.copy.save()

    def test_untranslated_copy_noindex_and_source_canonical(self):
        html = self.client.get(self.copy.url).content.decode()
        self.assertIn('<meta name="robots" content="noindex,follow">', html)
        self.assertIn(f'<link rel="canonical" href="{self.post.full_url}">', html)

    def test_untranslated_copy_absent_from_alternates(self):
        from seo.templatetags.seo_tags import alternates
        self.assertNotIn(("fr", self.copy.full_url), alternates(self.post))

    def test_untranslated_copy_absent_from_sitemap(self):
        self.assertNotIn(self.copy.full_url, self.client.get("/sitemap.xml").content.decode())

    def test_sitemap_only_contains_routable_urls(self):
        from xml.etree import ElementTree
        root = ElementTree.fromstring(self.client.get("/sitemap.xml").content)
        urls = [node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertTrue(urls)
        self.assertTrue(all(url.startswith("http://testserver/") for url in urls), urls)

    def test_translated_copy_keeps_self_canonical_and_discovery(self):
        from seo.templatetags.seo_tags import alternates
        self.copy.title = "Une histoire"
        self.copy.save()
        html = self.client.get(self.copy.url).content.decode()
        self.assertNotIn('content="noindex,follow"', html)
        self.assertIn(f'<link rel="canonical" href="{self.copy.full_url}">', html)
        self.assertIn(("fr", self.copy.full_url), alternates(self.post))
        self.assertIn(self.copy.full_url, self.client.get("/sitemap.xml").content.decode())

    def test_home_metadata_in_both_locales(self):
        import json
        from bs4 import BeautifulSoup
        for page in (self.home, self.fr_home):
            with self.subTest(locale=page.locale.language_code):
                soup = BeautifulSoup(self.client.get(page.url).content, "html.parser")
                self.assertEqual(soup.title.get_text(strip=True), "吴长星的博客")
                self.assertTrue(soup.find("meta", attrs={"name": "description"})["content"])
                self.assertTrue(soup.find("meta", property="og:image")["content"])
                graph = json.loads(soup.find("script", type="application/ld+json").string)["@graph"]
                self.assertEqual([entry["@type"] for entry in graph], ["WebSite", "Person"])
                self.assertEqual(graph[1]["name"], "吴长星")
                self.assertEqual(graph[1]["url"], "https://aaron404.com/")


class HealthTests(TestCase):
    def test_health_checks_database_and_redis(self):
        from unittest.mock import patch
        with patch("django_rq.get_connection") as redis:
            with self.assertNumQueries(1):
                response = self.client.get("/healthz")
            self.assertEqual(response.content, b"ok")
            redis.return_value.ping.assert_called_once_with()


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                             "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class LoginThrottleTests(TestCase):
    def test_five_failures_lock_both_admin_logins_by_username_and_ip(self):
        from django.contrib.auth import get_user_model
        get_user_model().objects.create_superuser("fictional-editor", "editor@example.com", "correct-password")
        for path in ("/admin/login/", "/django-admin/login/"):
            with self.subTest(path=path):
                headers = {"HTTP_CF_CONNECTING_IP": "192.0.2.10" if path.startswith("/admin/") else "192.0.2.11",
                           "HTTP_X_FORWARDED_FOR": "192.0.2.99"}
                for _ in range(5):
                    self.client.post(path, {"username": "fictional-editor", "password": "wrong"}, **headers)
                response = self.client.post(path, {"username": "fictional-editor", "password": "correct-password"}, **headers)
                self.assertEqual(response.status_code, 429)
                headers["HTTP_CF_CONNECTING_IP"] = "192.0.2.12" if path.startswith("/admin/") else "192.0.2.13"
                self.assertEqual(self.client.post(path, {"username": "fictional-editor", "password": "correct-password"}, **headers).status_code, 302)
                self.client.logout()


class ProductionSettingsTests(TestCase):
    def test_production_hsts_and_wsgi_defaults(self):
        import os
        import subprocess
        import sys
        from pathlib import Path
        env = {**os.environ, "SECRET_KEY": "fictional-test-key-" * 4}
        result = subprocess.run([sys.executable, "-c", "from mysite.settings import production as s; assert s.SECURE_HSTS_SECONDS == 31536000; assert not s.SECURE_HSTS_INCLUDE_SUBDOMAINS; assert not s.SECURE_HSTS_PRELOAD"],
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"mysite.settings.production"', Path("mysite/wsgi.py").read_text())

    def test_production_requires_secret_key(self):
        import os
        import subprocess
        import sys
        env = {k: v for k, v in os.environ.items() if k != "SECRET_KEY"}
        env["PYTHON_DOTENV_DISABLED"] = "1"
        result = subprocess.run([sys.executable, "-c", "from unittest.mock import patch; patch('dotenv.load_dotenv').start(); import mysite.settings.production"],
                                env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("KeyError: 'SECRET_KEY'", result.stderr)
