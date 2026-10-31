"""Crawler-facing endpoints: robots.txt, sitemap.xml, llms.txt, RSS feed."""
from django.contrib.syndication.views import Feed
from django.http import HttpResponse
from wagtail.contrib.sitemaps import Sitemap
from wagtail.models import Page

from blog.models import BlogPage
from flex.models import Engineer
from .templatetags.seo_tags import SITE_NAME, page_description

PRIVATE_PATHS = ["/admin/", "/django-admin/", "/django-rq/", "/search/", "/api/"]


def posts(language="zh-hans"):
    return (
        Page.objects.live().public().type(BlogPage, Engineer)
        .filter(locale__language_code=language)
        .order_by("-first_published_at")
        .specific()
    )


def robots_txt(request):
    lines = ["User-agent: *", *[f"Disallow: {p}" for p in PRIVATE_PATHS], "",
             f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def llms_txt(request):
    lines = [f"# {SITE_NAME} ({request.get_host()})", "",
             "> 吴长星的个人博客：随笔、技术与思考。原文为中文，多数文章另有 10 种语言的译文。", "",
             f"- RSS: {request.build_absolute_uri('/feed/')}",
             f"- Sitemap: {request.build_absolute_uri('/sitemap.xml')}", "", "## Posts", ""]
    lines += [f"- [{p.title}]({p.full_url}): {page_description(p)}" for p in posts()]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


class AllLocalesSitemap(Sitemap):
    """Wagtail's default sitemap only walks the default site's tree; translations live in sibling trees."""

    def items(self):
        return Page.objects.live().public().filter(depth__gt=1).order_by("path").defer_streamfields().specific()


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
        return item.full_url

    def item_pubdate(self, item):
        return item.first_published_at
