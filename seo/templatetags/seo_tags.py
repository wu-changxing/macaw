"""Per-page <head> metadata: description, canonical, hreflang, Open Graph, JSON-LD."""
import json

from django import template
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()

AUTHOR = "吴长星"
SITE_NAME = "吴长星的博客"


def page_description(page):
    if page.search_description:
        return page.search_description
    page = page.specific
    if hasattr(page, "body"):
        html = str(page.body)
    elif hasattr(page, "content"):
        html = str(page.content)
    else:
        html = getattr(page, "intro", "") or ""
    text = " ".join(strip_tags(html).split())
    return Truncator(text).chars(150)


def hreflang(code):
    return "zh-Hans" if code == "zh-hans" else code


def alternates(page):
    pages = [page, *page.get_translations().live()]
    links = [(hreflang(p.locale.language_code), p.full_url) for p in pages]
    source = next((p for p in pages if p.locale.language_code == "zh-hans"), page)
    return links + [("x-default", source.full_url)]


def cover_url(page):
    cover = getattr(page.specific, "cover_image", None)
    return page.get_site().root_url + cover.url if cover else ""


def article_ld(page, description, image):
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": page.title,
        "description": description,
        "url": page.full_url,
        "inLanguage": page.locale.language_code,
        "datePublished": page.specific.date.isoformat(),
        "dateModified": (page.last_published_at or page.first_published_at or page.specific.date).isoformat(),
        "author": {"@type": "Person", "name": AUTHOR, "url": page.get_site().root_url + "/"},
    }
    if image:
        data["image"] = image
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


@register.inclusion_tag("seo/head.html")
def seo_head(page):
    description = page_description(page)
    image = cover_url(page)
    is_article = getattr(page.specific, "date", None) is not None
    return {
        "page": page,
        "site_name": SITE_NAME,
        "description": description,
        "image": image,
        "is_article": is_article,
        "alternates": alternates(page),
        "json_ld": article_ld(page, description, image) if is_article else "",
    }
