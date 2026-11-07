"""Revoke legacy DRF tokens, including tables left after removing the app."""
from django.db import migrations


def delete_legacy_tokens(apps, schema_editor):
    connection = schema_editor.connection
    if "authtoken_token" in connection.introspection.table_names():
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM authtoken_token")


class Migration(migrations.Migration):
    dependencies = [("seo", "0001_site_https")]
    operations = [migrations.RunPython(delete_legacy_tokens, migrations.RunPython.noop)]
