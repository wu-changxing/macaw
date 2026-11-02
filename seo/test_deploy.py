"""Exercise the deploy script with local command doubles; never use SSH or services."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from textwrap import dedent

from django.test import SimpleTestCase


COMMAND = r'''
import os, pathlib, shlex, shutil, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
root = pathlib.Path(os.environ['HOME']) / 'project/blog'
revision = root / 'revision'
current = revision.read_text()
with (root / 'commands').open('a') as log:
    log.write(name + ' ' + ' '.join(args) + '\n')
failure = os.environ.get('DEPLOY_FAIL') if current == 'next' else ''
if name == 'git':
    if args[0] == 'rev-parse': print(current)
    if args[0] == 'reset': revision.write_text('next' if args[-1] == 'origin/main' else args[-1])
    if args[0] == 'log': print(current)
elif name == 'sqlite3':
    operation, backup = shlex.split(args[1])
    if operation == '.backup': shutil.copyfile(root / 'db.sqlite3', backup)
    if operation == '.restore': shutil.copyfile(backup, root / 'db.sqlite3')
elif name == 'uv':
    if failure == 'install': sys.exit(1)
elif name == 'python':
    if args[1] == 'migrate':
        (root / 'db.sqlite3').write_text('migrated')
        if failure == 'migrate': sys.exit(1)
    if args[1] == 'collectstatic' and failure == 'static': sys.exit(1)
    if args[1] == 'shell': print('/fictional-article/')
elif name == 'systemctl':
    if args[0] == 'is-active' and args[-1] == 'blog-worker' and failure == 'worker': sys.exit(1)
elif name == 'curl':
    url = args[-1]
    stage = 'health' if url.endswith('/healthz') else 'article'
    if failure == stage: sys.exit(1)
    print('ok')
'''


class DeploySafetyTests(SimpleTestCase):
    def run_deploy(self, home, failure=""):
        root = home / "project/blog"
        (root / "venv/bin").mkdir(parents=True)
        (home / ".local/bin").mkdir(parents=True)
        commands = home / "commands"
        commands.mkdir()
        (root / "revision").write_text("previous")
        (root / "db.sqlite3").write_text("original")
        for name in ("git", "sqlite3", "uv", "python", "systemctl", "curl"):
            path = commands / name
            path.write_text(f"#!{sys.executable}\n" + COMMAND)
            path.chmod(0o755)
        for path, target in ((root / "venv/bin/python", commands / "python"),
                             (home / ".local/bin/uv", commands / "uv")):
            path.symlink_to(target)
        (commands / "sudo").write_text('#!/bin/sh\nexec "$@"\n')
        (commands / "sleep").write_text('#!/bin/sh\nexit 0\n')
        (commands / "sudo").chmod(0o755)
        (commands / "sleep").chmod(0o755)
        script = Path("scripts/deploy.sh")
        body = script.read_text() if script.exists() else dedent(
            Path(".github/workflows/deploy.yml").read_text().split("script: |\n", 1)[1])
        return subprocess.run(["bash", "-c", body], env={**os.environ, "HOME": str(home),
                              "PATH": str(commands) + os.pathsep + os.environ["PATH"],
                              "DEPLOY_FAIL": failure}, capture_output=True, text=True)

    def test_success_checks_health_article_and_both_services_and_keeps_ten_backups(self):
        with TemporaryDirectory() as directory:
            home = Path(directory)
            backups = home / "backups"
            backups.mkdir()
            for n in range(12):
                (backups / f"pre-deploy-20200101{n:06d}.sqlite3").write_text("old")
            result = self.run_deploy(home)
            self.assertEqual(result.returncode, 0, result.stderr)
            root = home / "project/blog"
            log = (root / "commands").read_text()
            self.assertIn("/healthz", log)
            self.assertIn("/fictional-article/", log)
            self.assertIn("systemctl is-active --quiet blog\n", log)
            self.assertIn("systemctl is-active --quiet blog-worker\n", log)
            self.assertEqual(len(list(backups.iterdir())), 10)

    def test_each_post_reset_failure_restores_code_database_and_services(self):
        for failure in ("install", "migrate", "static", "health", "article", "worker"):
            with self.subTest(failure=failure), TemporaryDirectory() as directory:
                home = Path(directory)
                result = self.run_deploy(home, failure)
                self.assertNotEqual(result.returncode, 0)
                root = home / "project/blog"
                self.assertEqual((root / "revision").read_text(), "previous", result.stderr)
                self.assertEqual((root / "db.sqlite3").read_text(), "original")
                log = (root / "commands").read_text()
                recovery = log.split("git reset --hard previous\n", 1)[1]
                self.assertIn("uv pip install", recovery)
                self.assertIn("sqlite3 db.sqlite3 .restore", recovery)
                self.assertIn("systemctl restart blog blog-worker", recovery)
