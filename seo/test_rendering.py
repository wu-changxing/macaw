"""Render each public page type and exercise expensive-resource decisions."""
from datetime import date

from django.test import override_settings
from flex.models import Engineer
from seo.test_metadata import PageFixture


class RenderingTests(PageFixture):
    def test_original_floating_paper_and_home_card_grid(self):
        from home.models import HomeItem, HomeItemOrderable

        item = HomeItem.objects.create(name="Orchard", link=self.index.url,
                                       intro="Fruit notes", fa="fa-solid fa-book")
        HomeItemOrderable.objects.create(page=self.home, item=item)
        with self.subTest(page="article"):
            soup = self.soup(self.post)
            paper = soup.select_one("#article .shadow-2xl.bg-white")
            self.assertIsNotNone(paper, "Article must float on its original white paper sheet")
            self.assertIsNotNone(paper.select_one("#article-content.text-2xl.leading-loose"))
            self.assertIn("bg-gray-100", soup.select_one("#article")["class"])
        with self.subTest(page="home"):
            soup = self.soup(self.home)
            grid = soup.select_one("#items .grid")
            self.assertIsNotNone(grid, "Home must retain the original card grid")
            self.assertIn("xl:grid-cols-3", grid["class"])
            self.assertIsNotNone(grid.select_one("a.shadow-md.bg-white"))
            self.assertIsNotNone(grid.select_one(".text-sky-400 .fa-book"))

    def test_mathjax_only_for_rendered_math_delimiters(self):
        for body, expected in (("<p>Plain prose.</p>", False), (r"<p>Inline \(x\).</p>", True),
                               (r"<p>Display \[x\].</p>", True), ("<p>$$x$$</p>", True)):
            with self.subTest(body=body):
                self.post.body = body
                self.post.save()
                soup = self.soup(self.post)
                self.assertEqual(bool(soup.find("script", id="MathJax-script")), expected)
                self.assertEqual(bool(soup.find("script", src="/static/js/mathconfig.js")), expected)
        stream = self.index.add_child(instance=Engineer(title="Fictional equation", slug="equation", date=date(2026, 1, 2),
                                                       content=[("math", "x+y")]))
        self.assertTrue(self.soup(stream).find("script", id="MathJax-script"))
        for path in (self.home.url, self.index.url, "/search/", self.post.url + "?type=share"):
            html = self.client.get(path).content.decode()
            self.assertEqual("MathJax-script" in html, path.endswith("?type=share"))

    def test_fontawesome_deferred_with_noscript_and_llm_discovery(self):
        for page in (self.home, self.post):
            with self.subTest(page=page.title):
                soup = self.soup(page)
                links = soup.find_all("link", href=lambda href: href and "font-awesome" in href)
                self.assertEqual(len(links), 2)
                self.assertEqual(links[0]["media"], "print")
                self.assertEqual(links[0]["onload"], "this.media='all'")
                self.assertEqual(links[1].parent.name, "noscript")
                self.assertTrue(soup.find("link", type="text/plain", title="LLM summary"))

    def test_original_index_background_cover_and_share_image(self):
        from bs4 import BeautifulSoup
        soup = self.soup(self.index)
        self.assertIsNotNone(soup.find(style="background-image: url(/media/covers/fictional.png)"))
        soup = BeautifulSoup(self.client.get(self.post.url + "?type=share").content, "html.parser")
        image = soup.find("img", src="/media/covers/fictional.png")
        self.assertIsNotNone(image)
        self.assertEqual(image["decoding"], "async")

    @override_settings(DEBUG=False)
    def test_one_h1_and_main_and_machine_readable_dates(self):
        from bs4 import BeautifulSoup
        stream = self.index.add_child(instance=Engineer(title="Fictional invitation", slug="invitation", date=date(2026, 1, 2),
            content=[("cta", {"title": "Read more", "text": "<p>Some fruit notes.</p>", "button_text": "Read"})]))
        paths = (self.home.url, self.index.url, self.post.url, stream.url,
                 self.post.url + "?type=share", stream.url + "?type=share",
                 "/search/", "/search/?query=unlikelyword", "/missing-fictional-page/")
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404 if path.startswith("/missing-") else 200)
                soup = BeautifulSoup(response.content, "html.parser")
                self.assertEqual(len(soup.find_all("h1")), 1)
                self.assertEqual(len(soup.find_all("main")), 1)
                if path.startswith((self.index.url, self.post.url, stream.url)):
                    self.assertTrue(soup.find("time", datetime="2026-01-02"))

    def test_math_detection_uses_visible_text_and_decodes_entities(self):
        for body, expected in (("<p>&#92;(x&#92;)</p>", True),
                               ('<a href="/?q=\\(hidden">Plain prose</a>', False)):
            with self.subTest(body=body):
                self.post.body = body
                self.post.save()
                self.assertEqual(bool(self.soup(self.post).find("script", id="MathJax-script")), expected)
