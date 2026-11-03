# Macaw

The source code of [aaron404.com](https://aaron404.com), a personal, multilingual blog built on Django and Wagtail.

Posts are written in Simplified Chinese. Wagtail Localize and a Gemini translator plugin machine-translate them into 11 more locales. Readers can subscribe by email and comment by signing with an Ethereum wallet.

- Django 6.1.2, Wagtail 8.1, Python 3.14
- SQLite
- Redis + django-rq for background jobs
- Tailwind CSS 3 for styling (compiled into a static file, no Node at runtime)

## Features

**Writing**
- Two page types: `BlogPage` (one rich-text body) and the "Engineering page" `flex.Engineer` (a StreamField with paragraphs, quotes, poems, cards, call-to-action blocks, buttons, code blocks with syntax highlighting, and LaTeX math)
- More than one author per post (author snippets)
- Extra rich-text features in the editor: highlight (`<mark>`), inline code, centred text
- Optional word-cloud cover image, built in the background from the post's keywords (jieba + wordcloud, CJK font included)

**Multilingual**
- Locales: zh-hans (source), zh-hant, en, ja, ko, fr, de, es, it, pt, ru, ar
- Machine translation through `wagtail-localize`, using the `GPTPlugins.models.GeminiTranslator` backend (Gemini). Translation jobs run on the RQ queue.
- `scripts/click_translation.py` is a Selenium helper that walks the posts in the admin and runs translation for each locale

**Readers**
- Email subscriptions at `/subscribe/new/`. Subscribers are listed in the Wagtail admin. Tick "notify subscribers" on a post to email everyone in the background.
- Sign-to-comment: a reader signs the comment with an Ethereum wallet (MetaMask `personal_sign`, so no gas is spent). The server recovers the signer with `eth-account`. It rejects signatures that are older than 10 minutes, replayed, or don't match the claimed address, and allows 5 comments per hour per address. Comments are moderated in Django admin with `is_visible`. The endpoint is `POST /comments/`.
- Site search at `/search/` (Wagtail database search backend)

**SEO and discovery**
- Every page gets a meta description, a canonical URL, hreflang links to all of its translations, Open Graph tags, and JSON-LD `BlogPosting` data
- `/sitemap.xml` (all locales), `/robots.txt`, `/feed/` (RSS), `/llms.txt` (a site summary for AI search engines), `/favicon.ico`

**API**
- Wagtail API v2 at `/api/v2/` (`pages`, `images`, `documents`)

## Architecture

```
Browser ──> Caddy (TLS) ──> gunicorn: mysite.wsgi ──> SQLite
                                  │
                                  └── enqueue ──> Redis ──> rqworker default
                                                             ├─ word-cloud covers
                                                             ├─ subscriber emails
                                                             └─ GPT translations
```

- Pages are rendered on the server with Django templates (`mysite/templates/`) and styled with a compiled Tailwind stylesheet (`mysite/static/css/main.css`)
- Anything slow is a `django_rq` job, so saving a page in the admin returns straight away
- URL prefixes: the default language (zh-hans) has none; other locales are served under `/<lang>/...` (`i18n_patterns`, `prefix_default_language=False`)

<details>
<summary>URL map</summary>

| Path | What |
|------|------|
| `/admin/` | Wagtail admin (writing, translating, subscribers) |
| `/django-admin/` | Django admin (comment moderation) |
| `/django-rq/` | RQ queue dashboard (staff only) |
| `/api/v2/` | Wagtail API |
| `/comments/` | Sign-to-comment endpoint (POST) |
| `/sitemap.xml`, `/robots.txt`, `/feed/`, `/llms.txt` | SEO and feeds |
| `/subscribe/new/` | Subscription form |
| `/search/` | Search |
| everything else | Wagtail page tree |

</details>

## Local development

You need Python 3.14 and Redis. Redis is only needed for background jobs (covers, emails, translations); browsing and editing work without it.

```bash
git clone https://github.com/wu-changxing/macaw.git
cd macaw
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # optional for local work, see "Configuration"
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver        # http://localhost:8000, admin at /admin/
```

Background jobs, in two more terminals:

```bash
redis-server
python manage.py rqworker default
```

`manage.py` uses `mysite.settings.dev` by default. That file sets `DEBUG = True`, allows all hosts, and prints emails to the console instead of sending them.

### Styles (Tailwind)

The compiled `mysite/static/css/main.css` is committed. Rebuild it only after you change the classes used in templates:

```bash
cd tailwind
npm install
npm run build     # or: npm run watch
```

### Tests

```bash
python manage.py test
```

## Configuration

There are two places for configuration. Neither one is committed.

**`.env`** (loaded by python-dotenv; copy it from [`.env.example`](.env.example))

| Variable | Used for |
|----------|----------|
| `GEMINI_API_KEY` | Gemini machine translation |
| `GEMINI_MODEL` | Optional model override (default `gemini-3.8-flash`) |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP for subscriber emails (production; in dev, emails go to the console) |
| `EMAIL_BACKEND` | Overrides the Django email backend |
| `USERNAME`, `PASSWORD` | Admin login, used only by `scripts/click_translation.py` |

**`mysite/settings/secret.py`** (gitignored; production only, imported by `mysite/settings/production.py`)

```python
DJANGO_SECRET_KEY = "a long random string"
```

To generate one: `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`.

Settings layout:
- `mysite/settings/base.py`: shared settings (apps, locales, RQ, email)
- `mysite/settings/dev.py`: local development
- `mysite/settings/production.py`: `DEBUG = False`, allowed hosts, CORS, secure cookies behind the proxy. Select it with `DJANGO_SETTINGS_MODULE=mysite.settings.production`.

## Deployment

Each push to `main` deploys to production through [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The workflow connects to the server over SSH and runs these steps:

1. Back up SQLite, then fetch and reset to `origin/main`.
2. Compare the venv Python version with `.python-version`. If it differs, build a relocatable `venv.new`, install requirements, and swap the old environment into `venv.prev`.
3. Stop both services, then run `migrate` and `collectstatic` with production settings.
4. Restart `blog` (Gunicorn) and `blog-worker` (RQ), and check both services, `/healthz`, and an existing article.
5. On failure, restore the previous code, database backup and Python environment.

The operator must configure the Gunicorn systemd command to use `-c gunicorn.conf.py`. The configuration binds to loopback with three workers and four threads per worker.

The workflow reads three repository secrets: `SERVER_HOST`, `SERVER_USER`, and `SERVER_SSH_KEY`. You can also start it by hand with `workflow_dispatch`.

Because pushing to `main` deploys to production, all work goes through a branch and a pull request.

## Project layout

```
blog/          BlogPage, BlogIndexPage, authors, rich-text hooks; tasks/ = cover + email jobs
flex/          "Engineering page" (StreamField + code blocks + math)
streams/       StreamField block definitions used by flex
home/          HomePage and homepage item snippets
subscribe/     Subscriber model, form, and admin listing
comments/      Wallet sign-to-comment
seo/           Meta tags, sitemap, robots.txt, RSS, llms.txt
search/        Search view
GPTPlugins/    Gemini machine translator for wagtail-localize
mysite/        Settings, URLs, API router, templates, static files
tailwind/      Tailwind config and build scripts for main.css
frontend/      Source of the older React wallet widget (bundle in mysite/static/js)
scripts/       Selenium helper for batch translation
```

## Contributing

Issues and pull requests are welcome.

1. Fork the repo and create a branch from `main`
2. Keep each change small and focused, and say in the PR what you changed and how you tested it
3. Run `python manage.py test` before you open the PR
4. If you change model fields, include the migration (`python manage.py makemigrations`)

Never commit secrets. `.env`, `secret.py`, and `db.sqlite3` are gitignored; keep them that way.

## License

[MIT](LICENSE) © 2022-2026 Changxing Wu
