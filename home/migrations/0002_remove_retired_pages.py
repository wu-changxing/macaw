from django.db import migrations
from django.db.models import F, Q


def delete_page_trees(pages, ids):
    # Historical Page models have no treebeard methods. Delete leaves first and
    # maintain numchild exactly as treebeard does; surviving paths stay valid.
    for page in pages.filter(pk__in=ids).order_by("-depth", "path"):
        if pages.filter(path__startswith=page.path).exclude(pk__in=ids).exists():
            raise RuntimeError("A retired page has descendants that must be preserved.")
    if pages.filter(pk__in=ids, live=True).exists():
        raise RuntimeError("A retired page or alias is live; review before deleting it.")
    for pk, path, depth in pages.filter(pk__in=ids).order_by("-depth").values_list("pk", "path", "depth"):
        step = len(path) // depth
        pages.filter(pk=pk).delete()
        pages.filter(path=path[:-step]).update(numchild=F("numchild") - 1)


def delete_unused_content_types(content_types, connection):
    candidates = content_types.filter(
        Q(app_label__in=["feed", "eac_gift", "echo_atrium", "word_quiz"])
        | Q(app_label="flex", model="flexpage")
        | Q(app_label="subscribe", model="subscribepage")
    )
    ids = set(candidates.values_list("pk", flat=True))
    if not ids:
        return
    referenced = set()
    quote = connection.ops.quote_name
    placeholders = ", ".join(["%s"] * len(ids))
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names(cursor):
            constraints = connection.introspection.get_constraints(cursor, table)
            for constraint in constraints.values():
                if constraint.get("foreign_key") == ("django_content_type", "id"):
                    column = quote(constraint["columns"][0])
                    cursor.execute(
                        f"SELECT DISTINCT {column} FROM {quote(table)} "
                        f"WHERE {column} IN ({placeholders})", list(ids)
                    )
                    referenced.update(row[0] for row in cursor.fetchall())
    # Keep types referenced by permissions, logs, or any other installed/legacy
    # table. Deleting them through Django's collector would cascade those rows.
    candidates.filter(pk__in=ids - referenced).delete()


def remove_retired_pages(apps, schema_editor):
    connection = schema_editor.connection
    db = connection.alias
    content_types = apps.get_model("contenttypes", "ContentType").objects.using(db)
    pages = apps.get_model("wagtailcore", "Page").objects.using(db)
    retired_types = content_types.filter(app_label__in=["feed", "eac_gift"])
    orphan_ids = set(pages.filter(content_type__in=retired_types).values_list("pk", flat=True))
    ids = orphan_ids.copy()
    while aliases := set(pages.filter(alias_of_id__in=ids).values_list("pk", flat=True)) - ids:
        ids.update(aliases)

    tables = connection.introspection.table_names()
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        for app_label, model in retired_types.values_list("app_label", "model"):
            table = f"{app_label}_{model}"
            if table in tables:
                cursor.execute(
                    f"DELETE FROM {quote(table)} WHERE page_ptr_id IN "
                    f"(SELECT id FROM {quote(pages.model._meta.db_table)} "
                    "WHERE content_type_id IN (SELECT id FROM django_content_type "
                    "WHERE app_label IN (%s, %s)))", ["feed", "eac_gift"]
                )

    page_type = content_types.get(app_label="wagtailcore", model="page")
    apps.get_model("wagtailcore", "Revision").objects.using(db).filter(
        Q(content_type__in=retired_types)
        | Q(base_content_type_id=page_type.pk, object_id__in=[str(pk) for pk in ids])
    ).delete()
    delete_page_trees(pages, ids - orphan_ids)
    delete_page_trees(pages, orphan_ids)
    delete_unused_content_types(content_types, connection)


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0001_initial"),
        ("wagtailcore", "0098_apitoken"),
    ]
    operations = [migrations.RunPython(remove_retired_pages, migrations.RunPython.noop)]
