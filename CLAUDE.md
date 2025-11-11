# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Macaw is a Django-based CMS backend for the EchoAtrium Community, built with Wagtail. It provides content management, real-time messaging, background task processing, and multi-language support.

**Tech Stack:**
- Django 4.0.7 with Wagtail 5.1 CMS
- Django REST Framework for API endpoints
- Redis (via django-rq) for background task queues
- Socket.IO for real-time messaging
- SQLite database (development)
- Frontend: Tailwind CSS with Node.js build tools

## Development Commands

### Python/Django Commands

**Run development server:**
```bash
python manage.py runserver
```

**Run migrations:**
```bash
python manage.py migrate
```

**Create migrations:**
```bash
python manage.py makemigrations
```

**Create superuser:**
```bash
python manage.py createsuperuser
```

**Django shell:**
```bash
python manage.py shell
```

**Run tests:**
```bash
python manage.py test
```

**Test specific app:**
```bash
python manage.py test blog
python manage.py test streams
```

### Frontend/Tailwind Commands

Navigate to `/frontend` directory first:

**Watch mode (development):**
```bash
npm run watch
```

**Build CSS:**
```bash
npm run build
```

**Deploy CSS to static:**
```bash
npm run deploy
```

### Background Tasks

**Start Redis (required for background tasks):**
```bash
redis-server
```

**Start RQ worker:**
```bash
python manage.py rqworker default
```

**Monitor RQ dashboard:**
Access at `http://localhost:8000/django-rq/` when server is running.

## Project Architecture

### Settings Configuration

- Settings split into multiple files in `mysite/settings/`:
  - `base.py` - Base configuration shared across environments
  - `dev.py` - Development settings (default, sets DEBUG=True)
  - `production.py` - Production settings
  - `secret.py` - Secret keys (gitignored)
- Default: `manage.py` uses `mysite.settings.dev`
- Environment variables loaded from `.env` file via python-dotenv

### Core Django Apps

**blog/** - Main blogging functionality
- Models: `BlogPage`, `BlogIndexPage`, `BlogAuthor`
- Features: Auto-generate word cloud covers, email notifications to subscribers, multi-author support
- Background tasks in `blog/tasks/`: keyword extraction, word cloud generation, email sending
- Uses django-rq for async task processing

**streams/** - Wagtail StreamField blocks for flexible page content
- Located in `streams/blocks.py`
- Provides reusable content blocks for pages

**subscribe/** - Email subscription system
- Subscriber model and management
- Integrates with blog post notifications

**GPTPlugins/** - ChatGPT integration
- `models.py`: ChatGPT translator for Wagtail localization
- `gpt_request_handler.py`: OpenAI API integration
- `token_calculation.py`: Token counting utilities
- Used for translating blog content across 10+ languages

**home/** - Homepage and site entry point
- Wagtail homepage model

**flex/** - Additional flexible page types
- Custom Wagtail page models

**search/** - Site-wide search functionality
- Search view at `/search/`

### API Structure

**REST API** (mysite/api.py):
- Wagtail API v2 endpoints at `/api/v2/`
- Endpoints: pages, images, documents
- Token authentication enabled via DRF

**URL Configuration** (mysite/urls.py):
- Non-i18n routes: API, admin, Django RQ
- i18n routes: search, Wagtail pages
- Language prefix disabled by default (`prefix_default_language=False`)

### Background Job System

**Django-RQ** (Redis Queue):
- Replaced Celery for task management
- Queue configuration in `base.py`: `RQ_QUEUES` on localhost:6379
- Tasks decorated with `@job` from `django_rq`
- Example: `blog/tasks/tasks.py` - keyword extraction and word cloud generation

**Key Background Tasks:**
1. Word cloud generation from blog post content (uses jieba for Chinese text)
2. Email notifications to subscribers
3. Translation jobs via Wagtail Localize + ChatGPT

### Frontend Architecture

**Tailwind CSS Setup:**
- Source: `frontend/input.css`
- Output: `mysite/static/css/main.css`
- Build process copies templates from `mysite/templates/` to `frontend/prepare/`
- Uses `@tailwindcss/typography` plugin
- Syntax highlighting: `tailwind-highlightjs` package

**Static Files:**
- Development: served via Django staticfiles
- Production: collected to `static/` directory
- Media files: uploaded to `media/` directory
- Static root: `/static/`, Media root: `/media/`

### Database & Models

**SQLite** (db.sqlite3):
- Used for development
- Wagtail page tree structure
- User authentication, content, subscriptions

**Key Model Patterns:**
- Wagtail Page models inherit from `wagtail.models.Page`
- Custom save logic in `CoverForm` (blog/models.py) for background tasks
- API serialization via Wagtail APIField and DRF serializers

### Localization

**Multi-language Support:**
- 10+ languages configured in `WAGTAIL_CONTENT_LANGUAGES`
- Wagtail Localize for translation workflow
- ChatGPT-powered machine translation (`GPTPlugins.models.ChatGPTTranslator`)
- Currently `WAGTAIL_I18N_ENABLED = False` in base settings

### Email System

**Configuration:**
- Dev: Console backend (prints to terminal)
- Production: SMTP via environment variables
- Used for: subscriber notifications when new blog posts are published

### Code Organization Principles

**From user's CLAUDE.md preferences:**
- Avoid `utils.py` or `helper.py` - keep helper functions with the feature they support
- Don't use try-except blocks unless explicitly needed - let programs crash to see errors
- Keep functions small and focused
- Prefer simplicity over over-engineering

## Important Files

- `manage.py` - Django management script (uses dev settings)
- `daphne_manage.py` - ASGI server entry point for Socket.IO
- `requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies for Tailwind
- `.env` - Environment variables (gitignored, contains secrets)
- `mysite/urls.py` - URL routing configuration
- `mysite/api.py` - Wagtail API router setup

## Testing Notes

- Test files expected in each app (e.g., `blog/tests.py`)
- Some test files deleted (e.g., `streams/tests.py` in git status)
- Use `python manage.py test <app_name>` for app-specific tests

## Current Branch

Working branch: `newBlog`
Main branch: `master`

## Additional Context

- Redis required for background tasks (RQ workers)
- Wagtail admin at `/admin/`
- Django admin at `/django-admin/`
- Code blocks supported in Wagtail with syntax highlighting (okaidia theme)
- Real-time features use Socket.IO (python-socketio package)
- Word cloud generation uses Chinese font: SourceHanSerif
