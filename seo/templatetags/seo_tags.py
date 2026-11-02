"""Per-page <head> metadata: description, canonical, hreflang, Open Graph, JSON-LD."""
import json

from django import template
from django.conf import settings
from wagtail.models import Page
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()

AUTHOR = "吴长星"
SITE_NAME = "吴长星的博客"


def untranslated_source(page):
    """A same-title locale copy is still untranslated; return its source."""
    if page.locale.language_code == settings.LANGUAGE_CODE:
        return None
    source = Page.objects.filter(translation_key=page.translation_key,
                                 locale__language_code=settings.LANGUAGE_CODE).first()
    return source if source and source.title == page.title else None


def is_home(page):
    site = page.get_site()
    return ((page.depth == 2 and not getattr(page.specific, "date", None))
            or (site and page.translation_key == site.root_page.translation_key))


def page_description(page):
    if is_home(page):
        return ("吴长星的个人博客：随笔、技术与思考。" if page.locale.language_code.startswith("zh")
                else "Essays, technology and reflections by Changxing Wu.")
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
    pages = [page, *page.get_translations().live().public()]
    links = [(hreflang(p.locale.language_code), p.full_url) for p in pages if not untranslated_source(p)]
    source = next((p for p in pages if p.locale.language_code == settings.LANGUAGE_CODE), page)
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


def website_ld(description):
    data = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "url": "https://aaron404.com/", "description": description},
        {"@type": "Person", "name": AUTHOR, "url": "https://aaron404.com/"},
    ]}
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


@register.inclusion_tag("seo/head.html")
def seo_head(page):
    home = is_home(page)
    source = untranslated_source(page)
    description = page_description(page)
    image = cover_url(page) or ("https://aaron404.com/static/android-chrome-512x512.png" if home else "")
    is_article = getattr(page.specific, "date", None) is not None
    return {
        "page": page,
        "site_name": SITE_NAME,
        "title": SITE_NAME if home else page.seo_title or page.title,
        "canonical": (source or page).full_url,
        "noindex": source is not None,
        "description": description,
        "image": image,
        "is_article": is_article,
        "alternates": alternates(page),
        "json_ld": website_ld(description) if home else article_ld(page, description, image) if is_article else "",
    }
