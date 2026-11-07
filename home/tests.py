from importlib import import_module
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, override_settings
from wagtail.models import Page, Revision

from .models import HomePage


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class RetiredPageTests(TestCase):
    def test_cleanup_restores_parent_explorer_and_preserves_tree(self):
        parent = Page.get_first_root_node().add_child(instance=HomePage(
            title="Morgan's notebook", slug="morgan-notebook", banner="Field notes"))
        retired = parent.add_child(instance=Page(title="Retired", slug="retired", live=False))
        child = retired.add_child(instance=Page(title="Retired child", slug="retired-child", live=False))
        alias = parent.add_child(instance=Page(
            title="Retired alias", slug="retired-alias", live=False, alias_of=child))
        survivor = parent.add_child(instance=Page(title="Notes", slug="notes"))
        revision = child.save_revision()
        content_type = ContentType.objects.create(app_label="feed", model="feedpage")
        Page.objects.filter(pk__in=[retired.pk, child.pk]).update(content_type=content_type)
        self.assertIsNone(content_type.model_class())
        user = get_user_model().objects.create_superuser("morgan", "morgan@example.com", "fictional-password")
        self.client.force_login(user)

        migration = import_module("home.migrations.0002_remove_retired_pages")
        historical_apps = MigrationExecutor(connection).loader.project_state().apps
        migration.remove_retired_pages(historical_apps, SimpleNamespace(connection=connection))

        self.assertFalse(Page.objects.filter(pk__in=[retired.pk, child.pk, alias.pk]).exists())
        self.assertFalse(Revision.objects.filter(pk=revision.pk).exists())
        self.assertFalse(ContentType.objects.filter(pk=content_type.pk).exists())
        parent.refresh_from_db()
        self.assertEqual(parent.numchild, 1)
        self.assertEqual(parent.get_children().get().pk, survivor.pk)
        self.assertEqual(Page.find_problems(), ([], [], [], [], []))
        self.assertEqual(self.client.get(f"/admin/pages/{parent.pk}/").status_code, 200)

    def test_stale_content_types_are_removed_only_when_unreferenced(self):
        from django.contrib.auth.models import Permission

        used = ContentType.objects.create(app_label="echo_atrium", model="retiredentry")
        unused = ContentType.objects.create(app_label="word_quiz", model="retiredword")
        permission = Permission.objects.create(
            content_type=used, codename="view_retiredentry", name="View retired entry")
        migration = import_module("home.migrations.0002_remove_retired_pages")
        historical_apps = MigrationExecutor(connection).loader.project_state().apps
        migration.remove_retired_pages(historical_apps, SimpleNamespace(connection=connection))

        self.assertTrue(ContentType.objects.filter(pk=used.pk).exists())
        self.assertTrue(Permission.objects.filter(pk=permission.pk).exists())
        self.assertFalse(ContentType.objects.filter(pk=unused.pk).exists())
