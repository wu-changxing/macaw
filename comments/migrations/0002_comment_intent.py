"""Replay protection keys on the signed intent (signer + message), not the signature string.

The table was empty in production when this shipped; the guard below makes that assumption
explicit instead of silently giving existing rows a duplicate placeholder intent.
"""
from django.db import migrations, models


def require_empty(apps, schema_editor):
    count = apps.get_model("comments", "Comment").objects.count()
    if count:
        raise RuntimeError(f"comments_comment has {count} rows; backfill intent before adding the unique field")


class Migration(migrations.Migration):
    dependencies = [("comments", "0001_initial")]

    operations = [
        migrations.RunPython(require_empty, migrations.RunPython.noop),
        migrations.AlterField(model_name="comment", name="signature", field=models.CharField(max_length=132)),
        migrations.AddField(
            model_name="comment",
            name="intent",
            field=models.CharField(default="", help_text="sha256 of signer + signed message", max_length=64, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(model_name="comment", name="created_at", field=models.DateTimeField(auto_now_add=True, db_index=True)),
    ]
