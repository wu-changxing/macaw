"""Per-page <head> metadata: description, canonical, hreflang, Open Graph, JSON-LD."""
import json
import re
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit

from django import template
from django.conf import settings
from wagtail.models import Page
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()

AUTHOR = "吴长星"
SITE_NAME = "吴长星的博客"
AUTHOR_URL = "https://aaron404.com/"


def https_url(url):
    """Keep Wagtail's routed host/path, including translated paths, on HTTPS."""
    parts = urlsplit(url)
    return urlunsplit(parts._replace(scheme="https"))


def body_html(page):
    page = page.specific
    return str(getattr(page, "body", getattr(page, "content", "")))


def plain_text(html):
    """Keep block boundaries and decode entities after stripping markup."""
    html = re.sub(r"</(?:p|div|h[1-6]|li|blockquote|pre)>|<br\s*/?>", "\n", str(html), flags=re.I)
    return "\n".join(" ".join(line.split()) for line in unescape(strip_tags(html)).splitlines() if line.strip())


def author_url():
    page = Page.objects.live().public().filter(
        locale__language_code=settings.LANGUAGE_CODE,
        url_path__endswith="/my-moments-and-about/一个自我介绍/",
    ).first()
    return https_url(page.full_url) if page and page.full_url else AUTHOR_URL


def person():
    return {"@type": "Person", "@id": AUTHOR_URL + "#person", "name": AUTHOR,
            "alternateName": ["Changxing Wu", "Aaron"], "url": author_url(),
            "sameAs": ["https://github.com/wu-changxing"]}


def json_ld(data):
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))


def og_locale(code):
    return {"zh-hans": "zh_CN", "zh-hant": "zh_TW", "en": "en_US", "fr": "fr_FR",
            "es": "es_ES", "de": "de_DE", "ja": "ja_JP", "ko": "ko_KR", "pt": "pt_PT",
            "ru": "ru_RU", "ar": "ar_AR", "it": "it_IT"}[code]


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
        return " ".join(plain_text(page.search_description).split())
    page = page.specific
    if hasattr(page, "body"):
        html = str(page.body)
    elif hasattr(page, "content"):
        html = str(page.content)
    else:
        html = getattr(page, "intro", "") or ""
    text = " ".join(plain_text(html).split())
    return Truncator(text).chars(150)


def hreflang(code):
    return "zh-Hans" if code == "zh-hans" else code


def alternates(page):
    pages = [page, *page.get_translations().live().public()]
    links = [(hreflang(p.locale.language_code), https_url(p.full_url)) for p in pages if not untranslated_source(p)]
    source = next((p for p in pages if p.locale.language_code == settings.LANGUAGE_CODE), page)
    return links + [("x-default", https_url(source.full_url))]


def cover_url(page):
    cover = getattr(page.specific, "cover_image", None)
    return https_url(urljoin(page.get_site().root_url, cover.url)) if cover else ""


def word_count(page):
    """Count Han/Kana/Hangul characters individually, other text as word tokens."""
    text = re.sub(r"([\u3400-\u9fff\uf900-\ufaff\u3040-\u30ff\uac00-\ud7af])",
                  r" \1 ", plain_text(body_html(page)))
    return len(re.findall(r"\w+", text))


def section_index(page):
    """Articles can be nested beneath other articles; use the nearest section index."""
    from blog.models import BlogIndexPage
    return page.get_ancestors().type(BlogIndexPage).last()


def article_ld(page, description, image):
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": page.title.strip(),
        "description": description,
        "url": https_url((untranslated_source(page) or page).full_url),
        "mainEntityOfPage": https_url((untranslated_source(page) or page).full_url),
        "inLanguage": page.locale.language_code,
        "datePublished": page.specific.date.isoformat(),
        "dateModified": (page.last_published_at or page.first_published_at or page.specific.date).isoformat(),
        "author": person(),
        "publisher": person(),
        "articleSection": (section_index(page) or page.get_parent()).title,
        "wordCount": word_count(page),
    }
    if image:
        data["image"] = image
    return json_ld(data)


def breadcrumb_ld(page):
    page = untranslated_source(page) or page
    site = page.get_site()
    home = Page.objects.filter(translation_key=site.root_page.translation_key, locale_id=page.locale_id).first() or site.root_page
    parent = section_index(page) or page.get_parent()
    pages = [home] + ([parent] if parent.pk != home.pk and parent.depth > 1 else []) + [page]
    return json_ld({"@context": "https://schema.org", "@type": "BreadcrumbList",
                    "itemListElement": [{"@type": "ListItem", "position": i, "name": p.title,
                                         "item": https_url(p.full_url)} for i, p in enumerate(pages, 1)]})


def website_ld(description, language, page):
    from blog.models import BlogIndexPage
    sections = page.get_descendants().live().public().type(BlogIndexPage)
    data = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": SITE_NAME, "url": AUTHOR_URL, "description": description,
         "inLanguage": language, "hasPart": [
             {"@type": "CollectionPage", "name": section.title.strip(), "url": https_url(section.full_url)}
             for section in sections]},
        person(),
    ]}
    return json_ld(data)


@register.inclusion_tag("seo/head.html")
def seo_head(page):
    home = is_home(page)
    source = untranslated_source(page)
    description = page_description(page)
    image = cover_url(page) or ("https://aaron404.com/static/android-chrome-512x512.png" if home else "")
    is_article = getattr(page.specific, "date", None) is not None
    links = alternates(page)
    metadata = {
        "page": page,
        "site_name": SITE_NAME,
        "title": SITE_NAME if home else (page.seo_title or page.title).strip(),
        "canonical": https_url((source or page).full_url),
        "feed_url": https_url(urljoin(page.get_site().root_url, "/feed/")),
        "og_locale": og_locale(page.locale.language_code),
        "og_alternates": [og_locale(code.lower()) for code, url in links
                          if code not in (hreflang(page.locale.language_code), "x-default")],
        "modified": (page.last_published_at or page.first_published_at or getattr(page.specific, "date", None)),
        "author_url": author_url(),
        "breadcrumbs": breadcrumb_ld(page) if is_article else "",
        "noindex": source is not None,
        "description": description,
        "image": image,
        "is_article": is_article,
        "alternates": links,
        "json_ld": website_ld(description, page.locale.language_code, page) if home else article_ld(page, description, image) if is_article else "",
    }

    if https_url(page.full_url) == author_url() and not home:
        metadata["json_ld"] = json_ld({"@context": "https://schema.org", "@type": "ProfilePage",
                                        "url": https_url(page.full_url), "mainEntity": person()})
    return metadata


@register.simple_tag
def seo_title(page):
    if not page:
        return ""
    if is_home(page):
        return SITE_NAME
    suffix = SITE_NAME if page.locale.language_code.startswith("zh") else "Changxing Wu's blog"
    return f"{(page.seo_title or page.title).strip()} · {suffix}"


@register.inclusion_tag("seo/math.html")
def math_scripts(page):
    """Inspect rendered text, including delimiters added by StreamField math blocks."""
    text = plain_text(body_html(page)) if page else ""
    return {"has_math": any(delimiter in text for delimiter in (r"\(", r"\[", "$$"))}
