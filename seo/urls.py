from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from wagtail.contrib.sitemaps.views import sitemap

from . import views

# Crawler endpoints render every post (0.7–2s each on the 2-worker box); an hour of staleness is fine.
hourly = cache_page(60 * 60)

urlpatterns = [
    path("healthz", views.healthz),
    path("robots.txt", views.robots_txt),
    path("llms.txt", hourly(views.llms_txt)),
    path("llms-full.txt", hourly(views.llms_full_txt)),
    path("sitemap.xml", hourly(sitemap), {"sitemaps": {"pages": views.AllLocalesSitemap}, "template_name": "seo/sitemap.xml"}),
    path("feed/", hourly(views.PostsFeed())),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]
