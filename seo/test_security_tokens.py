from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase


class LegacyTokenMigrationTests(TransactionTestCase):
    def test_migration_deletes_existing_legacy_tokens(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("seo", "0001_site_https")])
        self.addCleanup(self.restore_migrations)
        created_table = "authtoken_token" not in connection.introspection.table_names()
        with connection.cursor() as cursor:
            if created_table:
                cursor.execute("CREATE TABLE authtoken_token (key varchar(40) PRIMARY KEY, created datetime, user_id integer)")
                self.addCleanup(self.drop_legacy_table)
            user = get_user_model().objects.create_user("fictional-token-owner")
            cursor.execute("INSERT INTO authtoken_token (key, created, user_id) VALUES (%s, %s, %s)",
                           ["fictional-token", "2026-01-01 00:00:00", user.pk])
        executor = MigrationExecutor(connection)
        executor.migrate([("seo", "0002_delete_legacy_tokens")])
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM authtoken_token")
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_migration_without_legacy_table(self):
        from importlib import import_module
        from unittest.mock import patch

        migration = import_module("seo.migrations.0002_delete_legacy_tokens")
        with connection.schema_editor() as editor:
            with patch.object(connection.introspection, "table_names", return_value=[]):
                with patch.object(connection, "cursor") as cursor:
                    migration.delete_legacy_tokens(None, editor)
                    cursor.assert_not_called()

    def drop_legacy_table(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE authtoken_token")

    def restore_migrations(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())


class PublicAPIAuthenticationTests(TestCase):
    def test_legacy_token_auth_is_disabled(self):
        self.assertNotIn("rest_framework.authtoken", settings.INSTALLED_APPS)
        self.assertNotIn("rest_framework.authentication.TokenAuthentication",
                         settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"])

    def test_public_pages_work_without_authentication_and_ignore_old_tokens(self):
        for headers in ({}, {"HTTP_AUTHORIZATION": "Token fictional-revoked-token"}):
            with self.subTest(headers=headers):
                response = self.client.get("/api/v2/pages/", secure=True, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertIn("items", response.json())
