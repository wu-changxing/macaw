# Contributing

Thanks for wanting to help. This is the source of a personal blog, so the bar is simple: changes should be small, tested, and true to how the site already works.

## Setup

You need Python 3.14 (see `.python-version`). Redis is optional; it is only needed to run background jobs.

```bash
git clone https://github.com/wu-changxing/macaw.git && cd macaw
python3.14 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver            # http://localhost:8000, admin at /admin/
```

`manage.py` uses `mysite.settings.dev`. Copy `.env.example` to `.env` only if you need translation or email; every value is optional locally.

Background jobs (word-cloud covers, newsletters, wagtail-localize jobs), in two more terminals:

```bash
redis-server
python manage.py rqworker default
```

Styles: `mysite/static/css/main.css` is compiled from the templates by Tailwind 3 and committed. Rebuild it only when you add or remove Tailwind classes in a template:

```bash
cd tailwind && npm install && npm run build
```

## Tests

```bash
python manage.py test                 # the whole suite, about two minutes
python manage.py test seo comments    # one or more apps
```

The suite needs neither Redis nor any API key. CI ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) runs the same command on Python 3.14 for every push and pull request, after `manage.py check` and `makemigrations --check`.

When you fix a bug, add a test that fails without your fix first. Tests and fixtures use fictional people and data only.

## Conventions

- **Keep helpers next to the feature that uses them.** Don't add `utils.py` or `helpers.py` modules.
- **Don't add `try/except` unless the error is expected and handled meaningfully.** Let unexpected errors surface.
- **Keep functions small and changes minimal.** Don't build something until it is needed.
- **Commit the migrations** that `python manage.py makemigrations` creates when you change a model.
- **Never commit secrets or personal data.** `.env`, `db.sqlite3` and `media/` are gitignored; keep them that way. The repository is public.
- **English** for code, comments, commit messages, issues and pull requests. Site content is written in Chinese.
- The home poster is generated: edit `home/blade/gen.py` and run it, don't edit `mysite/templates/home/blade_scene.html` by hand.

## Changing how the site looks

The reading design (the paper sheet, its shadow, the sky-blue theme colour, spacing and the page-turn arrows) was tuned by hand and is deliberately stable. See [docs/design.md](docs/design.md).

A pull request that could change rendering (templates, CSS, the Tailwind config, fonts, static-file settings, security headers) must include **before and after screenshots** of the home page, an article and a section index, at desktop (1440 px) and phone (about 390 px) widths. Visual changes are merged only with the author's approval. Backend-only changes should leave all of those files untouched.

## Pull request flow

1. Open an issue first for anything larger than a small fix, so we can agree on the approach.
2. Fork the repository and branch from `main`.
3. Keep the pull request to one change. Describe what changed, why, and how you tested it; the template will prompt you.
4. Make sure `python manage.py test` passes locally. CI must be green.
5. A merge to `main` deploys to production automatically ([`deploy.yml`](.github/workflows/deploy.yml)), so nothing is pushed to `main` directly; everything goes through review.

## Reporting bugs and security problems

Use the issue templates for bugs and feature ideas. Report security problems privately, as described in [SECURITY.md](SECURITY.md).

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
