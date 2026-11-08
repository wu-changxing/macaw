from django.apps import AppConfig
from wagtail.signals import page_published, page_unpublished


class SeoConfig(AppConfig):
    name = "seo"

    def ready(self):
        from .crawler_cache import invalidate_crawlers
        page_published.connect(invalidate_crawlers, dispatch_uid="seo-published")
        page_unpublished.connect(invalidate_crawlers, dispatch_uid="seo-unpublished")
