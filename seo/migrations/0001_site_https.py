"""Serve the aaron404.com Site on 443 so Wagtail's full_url (canonical, sitemap, API) is https."""
from django.db import migrations


def to_https(apps, schema_editor):
    apps.get_model("wagtailcore", "Site").objects.filter(hostname="aaron404.com", port=80).update(port=443)


def to_http(apps, schema_editor):
    apps.get_model("wagtailcore", "Site").objects.filter(hostname="aaron404.com", port=443).update(port=80)


class Migration(migrations.Migration):
    dependencies = [("wagtailcore", "0001_initial")]
    operations = [migrations.RunPython(to_https, to_http)]
