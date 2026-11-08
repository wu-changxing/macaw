from django.test import TestCase

# Create your tests here.


class LegacyCodeblockMigrationTests(TestCase):
    def test_list_shaped_codeblocks_become_structs(self):
        from importlib import import_module

        migration = import_module("flex.migrations.0004_upgrade_legacy_codeblocks")
        legacy = [
            {"type": "full_richtext", "value": "<p>Before</p>", "id": "a"},
            {"type": "codeblock", "id": "b", "value": [
                {"type": "code", "id": "c1", "value": {"language": "haskell", "code": "main = pure ()"}},
                {"type": "code", "id": "c2", "value": {"language": "python", "code": "print(1)"}},
            ]},
            {"type": "codeblock", "id": "d", "value": {"heading": "Kept", "code": {"language": "bash", "code": "ls"}}},
        ]
        upgraded = migration.upgrade_blocks(legacy)
        self.assertEqual(upgraded[0], legacy[0])
        self.assertEqual(upgraded[1], {"type": "codeblock", "id": "b", "value": {
            "heading": "", "code": {"language": "haskell", "code": "main = pure ()"}}})
        self.assertEqual(upgraded[2]["type"], "codeblock")
        self.assertEqual(upgraded[2]["value"], {"heading": "", "code": {"language": "python", "code": "print(1)"}})
        self.assertEqual(upgraded[3], legacy[2])
        self.assertEqual(len({block["id"] for block in upgraded}), 4)
