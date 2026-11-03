"""Crawler-facing endpoints: robots.txt, sitemap.xml, llms.txt, RSS feed."""
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.http import HttpResponse
from django.db import connection
import django_rq
from wagtail.contrib.sitemaps import Sitemap
from wagtail.models import Page, Site

from blog.models import BlogIndexPage, BlogPage
from flex.models import Engineer
from .templatetags.seo_tags import (SITE_NAME, body_html, cover_url, https_url,
                                    page_description, plain_text, section_index, untranslated_source)

PRIVATE_PATHS = ["/admin/", "/django-admin/", "/django-rq/", "/search/", "/api/"]


def posts(language=settings.LANGUAGE_CODE):
    return (
        Page.objects.live().public().type(BlogPage, Engineer)
        .filter(locale__language_code=language)
        .order_by("-first_published_at")
        .specific()
    )


def robots_txt(request):
    lines = ["User-agent: *", *[f"Disallow: {p}" for p in PRIVATE_PATHS], "",
             f"Sitemap: {https_url(request.build_absolute_uri('/sitemap.xml'))}"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def llms_description(page):
    text = " ".join(plain_text(page.search_description or body_html(page)).split())
    return text if page.search_description else text[:120]


def llms_txt(request):
    sections = BlogIndexPage.objects.live().public().filter(locale__language_code=settings.LANGUAGE_CODE).order_by("path")
    articles = list(posts())
    # Summarise actual section titles/descriptions; no inferred biography or translation counts.
    summary = "; ".join(section.title + (": " + " ".join(plain_text(section.intro).split()) if section.intro else "")
                        for section in sections)
    site = Site.find_for_request(request)
    summary = site.root_page.search_description or summary or site.root_page.title
    lines = [f"# {SITE_NAME}", "", " ".join(plain_text(summary).split()), "",
             f"- Full text: {https_url(request.build_absolute_uri('/llms-full.txt'))}",
             f"- RSS: {https_url(request.build_absolute_uri('/feed/'))}",
             f"- Sitemap: {https_url(request.build_absolute_uri('/sitemap.xml'))}"]
    grouped = {section.pk: [] for section in sections}
    for article in articles:
        section = section_index(article)
        grouped.setdefault(section.pk if section else None, []).append(article)
    headings = [(section.title, section.pk) for section in sections]
    if None in grouped:
        headings.append(("Posts", None))
    for title, key in headings:
        lines += ["", f"## {title}", ""]
        lines += [f"- [{p.title}]({https_url(p.full_url)}): {llms_description(p)}" for p in grouped[key]]
    english = [p for p in posts("en").filter(translation_key__in=[p.translation_key for p in articles])
               if not untranslated_source(p)]
    if english and settings.LANGUAGE_CODE != "en":
        lines += ["", "## English", ""]
        lines += [f"- [{p.title}]({https_url(p.full_url)}): {llms_description(p)}" for p in english]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def llms_full_txt(request):
    articles = [f"# {p.title}\n\nURL: {https_url(p.full_url)}\nDate: {p.date.isoformat()}\n\n{plain_text(body_html(p))}"
                for p in posts()]
    return HttpResponse("\n\n---\n\n".join(articles) + "\n", content_type="text/plain; charset=utf-8")


class AllLocalesSitemap(Sitemap):
    """Wagtail's default sitemap only walks the default site's tree; translations live in sibling trees."""

    def items(self):
        pages = Page.objects.live().public().filter(depth__gt=1).order_by("path").defer_streamfields().specific()
        excluded = [page.pk for page in pages if not page.full_url or untranslated_source(page)]
        return pages.exclude(pk__in=excluded)

    def _urls(self, page, protocol, domain):
        """Wagtail returns URL dictionaries; enrich them for our XML template."""
        urls = []
        for item in self.paginator.page(page).object_list:
            for entry in item.get_sitemap_urls(self.request):
                entry.update(location=https_url(entry["location"]), lastmod=item.last_published_at,
                             image=cover_url(item))
                urls.append(entry)
        return urls


class PostsFeed(Feed):
    title = SITE_NAME
    link = "/"
    description = "吴长星的随笔、技术与思考"

    def items(self):
        return posts()[:30]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return page_description(item)

    def item_link(self, item):
        return https_url(item.full_url)

    def item_pubdate(self, item):
        return item.first_published_at


def healthz(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    django_rq.get_connection("default").ping()
    return HttpResponse("ok", content_type="text/plain")
