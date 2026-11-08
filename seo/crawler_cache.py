"""One-hour crawler response caches, renewed after publication changes."""
from functools import wraps
from uuid import uuid4

from django.core.cache import cache
from django.db import transaction
from django.views.decorators.cache import cache_page

GENERATION_KEY = "seo:crawlers:generation"


def invalidate_crawlers(sender, **kwargs):
    transaction.on_commit(lambda: cache.set(GENERATION_KEY, uuid4().hex, timeout=None))


def hourly(view):
    @wraps(view)
    def cached(request, *args, **kwargs):
        generation = cache.get(GENERATION_KEY, "initial")
        response = cache_page(3600, key_prefix=f"seo:{generation}")(view)(request, *args, **kwargs)
        response["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
        return response
    return cached
