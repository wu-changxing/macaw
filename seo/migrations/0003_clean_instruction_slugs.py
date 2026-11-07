"""Repair only the three instruction-bearing slugs verified in the DB audit.

Identity + locale + exact old slug prevent broad substring matches from changing
ordinary pages. Historical Page has no set_url_path/save tree logic: replace the
URL prefix on the page and its descendants, leaving materialized tree paths alone.
"""
from django.conf import settings
from django.db import migrations

TARGETS = [
    (50, "en", "musings159-please-note-that-wherever-theres-b-or", "musings159"),
    (53, "en", "musings-164-please-note-that-wherever-theres-b-or", "musings-164"),
    (3852, "it", "previsione-si-prega-di-notare-che-ovunque-ci-sia-b-o", "previsione"),
]


def redirect_old_path(apps, alias, page, old_url):
    if "wagtailredirects" not in apps.app_configs:
        return
    Page = apps.get_model("wagtailcore", "Page")
    Site = apps.get_model("wagtailcore", "Site")
    Redirect = apps.get_model("wagtailredirects", "Redirect")
    for site in Site.objects.using(alias).all():
        root = Page.objects.using(alias).get(pk=site.root_page_id)
        localized = Page.objects.using(alias).filter(
            translation_key=root.translation_key, locale_id=page.locale_id).first()
        if localized and old_url.startswith(localized.url_path):
            code = apps.get_model("wagtailcore", "Locale").objects.using(alias).get(pk=page.locale_id).language_code
            prefix = "/" if code == settings.LANGUAGE_CODE else f"/{code}/"
            old_path = (prefix + old_url[len(localized.url_path):]).rstrip("/")
            Redirect.objects.using(alias).update_or_create(
                site_id=site.pk, old_path=old_path,
                defaults={"redirect_page_id": page.pk, "is_permanent": True})


def clean_slugs(apps, schema_editor):
    alias = schema_editor.connection.alias
    Page = apps.get_model("wagtailcore", "Page")
    pages = Page.objects.using(alias)
    for pk, language, old_slug, base in TARGETS:
        page = pages.filter(pk=pk, locale__language_code=language, slug=old_slug).first()
        if page is None:
            continue
        parent = pages.get(path=page.path[:-4])  # Wagtail MP tree steplen = 4.
        siblings = pages.filter(depth=page.depth, path__startswith=parent.path).exclude(pk=pk)
        slug, number = base, 2
        while siblings.filter(slug=slug).exists():
            slug, number = f"{base}-{number}", number + 1
        old_url = page.url_path
        new_url = parent.url_path + slug + "/"
        descendants = list(pages.filter(path__startswith=page.path).exclude(pk=pk))
        pages.filter(pk=pk).update(slug=slug, url_path=new_url)
        for child in descendants:
            pages.filter(pk=child.pk).update(url_path=new_url + child.url_path[len(old_url):])
        redirect_old_path(apps, alias, page, old_url)


class Migration(migrations.Migration):
    dependencies = [("seo", "0002_delete_legacy_tokens"),
                    ("wagtailredirects", "0008_add_verbose_name_plural")]
    operations = [migrations.RunPython(clean_slugs, migrations.RunPython.noop)]
