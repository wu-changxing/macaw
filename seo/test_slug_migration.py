from datetime import date
from wagtail.models import Locale
from blog.models import BlogPage
from seo.test_metadata import PageFixture


class SlugMigrationTests(PageFixture):
    def test_slug_migration_historical_models_collision_descendants_redirect(self):
        from importlib import import_module
        from django.apps import apps
        from django.db import connection
        from django.db.migrations.state import ProjectState
        from wagtail.contrib.redirects.models import Redirect
        en = Locale.objects.create(language_code='en')
        home = self.home.copy_for_translation(en)
        index = self.index.copy_for_translation(en)
        old_slug = 'musings159-please-note-that-wherever-theres-b-or'
        post = index.add_child(instance=BlogPage(title='Fictional notes', slug=old_slug, date=date(2026, 1, 1)))
        index.add_child(instance=BlogPage(title='Fictional collision', slug='musings159', date=date(2026, 1, 1)))
        child = post.add_child(instance=BlogPage(title='Fictional child', slug='child', date=date(2026, 1, 1)))
        old_url = post.url
        migration = import_module('seo.migrations.0003_clean_instruction_slugs')
        original_targets = migration.TARGETS
        self.addCleanup(setattr, migration, 'TARGETS', original_targets)
        migration.TARGETS = [(post.pk, 'en', old_slug, 'musings159')]
        historical = ProjectState.from_apps(apps).apps
        migration.clean_slugs(historical, connection.schema_editor())
        post.refresh_from_db()
        child.refresh_from_db()
        self.assertEqual(post.slug, 'musings159-2')
        self.assertEqual(post.title, 'Fictional notes')
        self.assertEqual(child.url_path, post.url_path + 'child/')
        redirect = Redirect.objects.get(old_path=old_url.rstrip('/'))
        self.assertEqual(redirect.redirect_page_id, post.id)
        self.assertTrue(redirect.is_permanent)
        migration.clean_slugs(historical, connection.schema_editor())
        self.assertEqual(Redirect.objects.filter(redirect_page=post).count(), 1)

