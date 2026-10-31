from django.test import TestCase, override_settings
from django.utils import timezone
from wagtail.models import Page, Site

from blog.models import BlogPage


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
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
