# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## What this is

The source code of the blog at https://aaron404.com: Django 6.1.3 + Wagtail 8.1, Python 3.14, SQLite. Posts are written in Simplified Chinese and machine-translated with wagtail-localize and a Gemini translator. Background jobs run on django-rq + Redis. The repo is public, so never commit secrets, server addresses, or personal data.

## Commands

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver            # uses mysite.settings.dev
python manage.py test                 # or: python manage.py test seo comments
python manage.py makemigrations       # commit the migrations it creates

redis-server                          # only needed for background jobs
python manage.py rqworker default

cd tailwind && npm install && npm run build   # rebuilds mysite/static/css/main.css
```

## Layout

- `blog/`: `BlogPage`, `BlogIndexPage`, `BlogAuthor` snippets, rich-text hooks (`wagtail_hooks.py`). `blog/tasks/` holds the RQ jobs: word-cloud cover (`tasks.py`, uses jieba) and subscriber emails (`send_email.py`).
- `flex/`: `Engineer` ("Engineering page"), a StreamField page whose blocks come from `streams/blocks.py`. It has code blocks and math.
- `home/`: `HomePage` + `HomeItem` snippets. `home/blade/gen.py` generates the home poster (`mysite/templates/home/blade_scene.html`); edit the generator, not its output.
- `docs/`: `architecture.md` and `design.md`, plus the README screenshots in `docs/images/`. Update them when behaviour they describe changes.
- `subscribe/`: `Subscriber` model, form at `/subscribe/new/`, admin listing.
- `comments/`: wallet sign-to-comment (`POST /comments/`, signature checked with `eth-account`, moderated with `is_visible` in Django admin).
- `seo/`: meta/canonical/hreflang/Open Graph/JSON-LD head tags, `/sitemap.xml`, `/robots.txt`, `/feed/`, `/llms.txt`, `/favicon.ico`.
- `GPTPlugins/`: `GeminiTranslator`, the `WAGTAILLOCALIZE_MACHINE_TRANSLATOR` backend (Gemini, `GEMINI_API_KEY`).
- `search/`: search view at `/search/`.
- `mysite/`: settings, `urls.py`, `api.py` (Wagtail API v2 at `/api/v2/`, pages endpoint only), templates, static files.
- `tailwind/`: Tailwind 3 + typography config. It compiles `mysite/static/css/main.css` from the templates.
- `frontend/`: source of the older React wallet widget. Its built bundle is `mysite/static/js/main.*.js`, included by `mysite/templates/wallet.html`.

## Settings

- `mysite/settings/base.py`: shared. Sets `LANGUAGE_CODE = "zh-hans"`, `WAGTAIL_I18N_ENABLED = True`, 12 locales in `WAGTAIL_CONTENT_LANGUAGES`, and `RQ_QUEUES` on localhost:6379.
- `mysite/settings/dev.py`: `DEBUG = True` and a console email backend. `manage.py` uses this by default.
- `mysite/settings/production.py`: `DEBUG = False`. Reads `SECRET_KEY` from the environment (`.env` on the server) and fails to start without it.
- `.env` is loaded by python-dotenv. `.env.example` lists the variable names.
- URLs: the default language has no prefix (`prefix_default_language=False`); other locales use `/<lang>/`.

## Deploy

A push to `main` triggers `.github/workflows/deploy.yml`, which deploys to production over SSH: reset to `origin/main`, `uv pip install`, `migrate`, `collectstatic`, restart the `blog` and `blog-worker` services, then a health check. Never push to `main` directly. Open a PR instead. `.github/workflows/tests.yml` runs `check`, `makemigrations --check` and the test suite on every push and PR.

## Known rough edges

- `mysite/asgi.py` imports `echo_atrium`, which no longer exists in this repo. Production runs WSGI (gunicorn), so use `mysite.wsgi`, not ASGI or `daphne_manage.py`.
- `mysite/celery.py` and `starcelery.sh` are left over from before the move to django-rq.
- `requirements.txt` is a full `pip freeze` and includes unused packages (jupyter, sanic, Telethon, ...).

## Conventions

- Keep helper functions next to the feature that uses them. Don't add new `utils.py`/`helpers.py` files.
- Don't use `try/except` unless it's really needed. Let errors surface.
- Keep functions small and changes minimal. Don't build anything until it's needed.
