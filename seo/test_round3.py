"""Round-three regressions on rendered crawler and reader paths."""
import json
from xml.etree import ElementTree as ET
from datetime import date

from wagtail.models import Locale
from blog.models import BlogIndexPage, BlogPage, BlogAuthor, BlogAuthorsOrderable
from seo.test_metadata import PageFixture
from seo.templatetags.seo_tags import https_url


class RoundThreeTests(PageFixture):
    def data(self, page):
        return [json.loads(s.string) for s in self.soup(page).find_all('script', type='application/ld+json')]

    def test_descriptions_decode_once_and_separate_chinese_blocks(self):
        self.post.body = '<p>林的&#x27;苹果 &amp; 梨</p><p>第二段中文</p>'
        self.post.save()
        expected = "林的'苹果 & 梨 第二段中文"
        soup = self.soup(self.post)
        for attrs in ({'name': 'description'}, {'property': 'og:description'}, {'name': 'twitter:description'}):
            self.assertEqual(soup.find('meta', attrs=attrs)['content'], expected)
        self.assertEqual(self.data(self.post)[0]['description'], expected)
        root = ET.fromstring(self.client.get('/feed/').content)
        self.assertEqual(root.find('.//item/description').text, expected)

    def test_person_profile_and_byline(self):
        about = self.home.add_child(instance=BlogIndexPage(title='About', slug='my-moments-and-about'))
        bio = about.add_child(instance=BlogPage(title='一个自我介绍', slug='一个自我介绍', date=date(2026, 1, 1)))
        graph = self.data(self.home)[0]['@graph']
        person = graph[1]
        self.assertEqual(person['@id'], 'https://aaron404.com/#person')
        self.assertEqual(person['alternateName'], ['Changxing Wu', 'Aaron'])
        self.assertEqual(person['url'], https_url(bio.full_url))
        profile = next(d for d in self.data(bio) if d['@type'] == 'ProfilePage')
        self.assertEqual(profile['mainEntity'], person)
        for key in ('author', 'publisher'):
            self.assertEqual(self.data(self.post)[0][key]['@id'], person['@id'])
            self.assertEqual(self.data(self.post)[0][key]['name'], person['name'])
        author = BlogAuthor.objects.create(name='Fictional Lin')
        BlogAuthorsOrderable.objects.create(page=self.post, author=author)
        link = self.soup(self.post).find('a', string=lambda s: s and 'Fictional Lin' in s)
        self.assertIn('author', link['rel'])
        self.assertEqual(link['href'], self.index.url)

    def test_trimmed_localized_titles(self):
        self.post.title = '  Fictional pears  '
        self.post.seo_title = '  Fictional fruit  '
        self.post.save()
        for page, suffix in ((self.post, '吴长星的博客'),):
            soup = self.soup(page)
            self.assertEqual(soup.title.string, f'Fictional fruit · {suffix}')
            self.assertEqual(soup.find('meta', property='og:title')['content'], 'Fictional fruit')
            self.assertEqual(soup.find('meta', attrs={'name': 'twitter:title'})['content'], 'Fictional fruit')
            self.assertEqual(self.data(page)[0]['headline'], 'Fictional pears')
        fr = Locale.objects.create(language_code='fr')
        home = self.home.copy_for_translation(fr)
        home.live = True
        home.save()
        index = self.index.copy_for_translation(fr)
        index.live = True
        index.save()
        copy = self.post.copy_for_translation(fr)
        copy.live = True
        copy.title = '  Poires  '
        copy.seo_title = ''
        copy.save()
        self.assertEqual(self.soup(copy).title.string, "Poires · Changxing Wu's blog")

    def test_untranslated_structured_urls_use_source(self):
        fr = Locale.objects.create(language_code='fr')
        home = self.home.copy_for_translation(fr)
        home.live = True
        home.save()
        index = self.index.copy_for_translation(fr)
        index.live = True
        index.save()
        copy = self.post.copy_for_translation(fr)
        copy.live = True
        copy.save()
        data, crumbs = self.data(copy)
        self.assertEqual(data['url'], https_url(self.post.full_url))
        self.assertEqual(data['mainEntityOfPage'], data['url'])
        self.assertEqual(crumbs, self.data(self.post)[1])

    def test_home_sections_and_no_search_action(self):
        draft = self.home.add_child(instance=BlogIndexPage(title='Draft', slug='draft', live=False))
        graph = self.data(self.home)[0]['@graph']
        self.assertEqual([p['url'] for p in graph[0]['hasPart']], [https_url(self.index.full_url)])
        self.assertNotIn('potentialAction', graph[0])

    def test_no_search_action(self):
        self.assertNotIn('potentialAction', self.data(self.home)[0]['@graph'][0])

    def test_llms_author_line(self):
        for path in ('/llms.txt', '/llms-full.txt'):
            self.assertIn('Author: 吴长星 (Changxing Wu, Aaron) — https://github.com/wu-changxing — about: https://aaron404.com/', self.client.get(path).content.decode())

    def test_sitemap_alternates(self):
        fr = Locale.objects.create(language_code='fr')
        home = self.home.copy_for_translation(fr)
        home.live = True
        home.save()
        index = self.index.copy_for_translation(fr)
        index.live = True
        index.save()
        copy = self.post.copy_for_translation(fr)
        copy.live = True
        copy.title = 'Poires'
        copy.save()
        root = ET.fromstring(self.client.get('/sitemap.xml').content)
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
        node = next(n for n in root if n.find('s:loc', ns).text == https_url(self.post.full_url))
        self.assertEqual({n.attrib['hreflang']: n.attrib['href'] for n in node.findall('x:link', ns)}, {'zh-Hans': https_url(self.post.full_url), 'fr': https_url(copy.full_url), 'x-default': https_url(self.post.full_url)})

    def test_rss_author(self):
        root = ET.fromstring(self.client.get('/feed/').content)
        self.assertEqual(root.find('.//item/{http://purl.org/dc/elements/1.1/}creator').text, '吴长星')

    def test_wallet_head_and_body_contract(self):
        soup = self.soup(self.post)
        self.assertEqual(len(soup.find_all('head')), 1)
        self.assertEqual(soup.find('link', href='/static/css/main.d7cb9a48.css').parent.name, 'head')
        self.assertEqual(str(soup.find(id='wallet')), '<div id="wallet"></div>')
        self.assertIsNotNone(soup.select_one('#article-content.text-2xl.leading-loose'))

    def test_wallet_stylesheet_preserves_cascade_order(self):
        links = [n.get('href') for n in self.soup(self.index).select('link[rel=stylesheet]')]
        self.assertLess(links.index('/static/css/post_index.css'), links.index('/static/css/main.d7cb9a48.css'))

    def test_share_dependency_order(self):
        soup = self.soup_path_share()
        dom = soup.find_all('script', src=lambda s: s and 'dom-to-image' in s)
        self.assertEqual(len(dom), 1)
        self.assertIn('defer', dom[0].attrs)
        self.assertIn('defer', soup.find('script', src=lambda s: s and 'FileSaver' in s).attrs)
        self.assertNotIn('defer', soup.find('script', src=lambda s: s and 'jquery' in s).attrs)

    def soup_path_share(self):
        from bs4 import BeautifulSoup
        return BeautifulSoup(self.client.get(self.post.url + '?type=share').content, 'html.parser')

    def test_empty_public_sitemap(self):
        from wagtail.models import Page
        Page.objects.all().update(live=False)
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(ET.fromstring(response.content)), 0)
