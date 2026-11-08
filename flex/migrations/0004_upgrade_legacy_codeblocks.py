"""Old code blocks were stored as a list of `code` children; the block is now one struct."""
import json
from uuid import uuid4

from django.db import migrations


def upgrade_codeblock(block):
    if not isinstance(block["value"], list):
        return [block]
    upgraded = []
    for index, child in enumerate(block["value"]):
        upgraded.append({
            "type": "codeblock",
            "id": block["id"] if index == 0 else str(uuid4()),
            "value": {"heading": "", "code": child["value"]},
        })
    return upgraded


def upgrade_blocks(blocks):
    upgraded = []
    for block in blocks:
        upgraded.extend(upgrade_codeblock(block) if block["type"] == "codeblock" else [block])
    return upgraded


def upgrade_pages(apps, schema_editor):
    Engineer = apps.get_model("flex", "Engineer")
    for page in Engineer.objects.all():
        blocks = list(page.content.raw_data)
        upgraded = upgrade_blocks(blocks)
        if upgraded != blocks:
            Engineer.objects.filter(pk=page.pk).update(content=json.dumps(upgraded))
    upgrade_revisions(apps)


def upgrade_revisions(apps):
    Revision = apps.get_model("wagtailcore", "Revision")
    ContentType = apps.get_model("contenttypes", "ContentType")
    engineer = ContentType.objects.filter(app_label="flex", model="engineer").first()
    if engineer is None:
        return
    for revision in Revision.objects.filter(content_type=engineer):
        stored = revision.content.get("content")
        if not stored:
            continue
        blocks = json.loads(stored) if isinstance(stored, str) else stored
        upgraded = upgrade_blocks(blocks)
        if upgraded != blocks:
            revision.content["content"] = json.dumps(upgraded)
            revision.save(update_fields=["content"])


class Migration(migrations.Migration):
    dependencies = [
        ("flex", "0003_alter_engineer_content"),
        ("wagtailcore", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(upgrade_pages, migrations.RunPython.noop)]
