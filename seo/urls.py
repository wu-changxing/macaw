from django.conf import settings
from django.urls import path
from django.views.generic import RedirectView
from wagtail.contrib.sitemaps.views import sitemap

from . import views
from .crawler_cache import hourly

urlpatterns = [
    path("healthz", views.healthz),
    path("robots.txt", hourly(views.robots_txt)),
    path("llms.txt", hourly(views.llms_txt)),
    path("llms-full.txt", hourly(views.llms_full_txt)),
    path("sitemap.xml", hourly(sitemap), {"sitemaps": {"pages": views.AllLocalesSitemap}, "template_name": "seo/sitemap.xml"}),
    path("feed/", hourly(views.PostsFeed())),
    path(f"{settings.LANGUAGE_CODE}/feed/", hourly(views.PostsFeed())),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
    path("apple-touch-icon.png", RedirectView.as_view(url="/static/apple-touch-icon.png", permanent=True)),
    path("apple-touch-icon-precomposed.png", RedirectView.as_view(url="/static/apple-touch-icon.png", permanent=True)),
]
