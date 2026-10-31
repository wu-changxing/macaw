from django.urls import path
from django.views.generic import RedirectView
from wagtail.contrib.sitemaps.views import sitemap

from . import views

urlpatterns = [
    path("robots.txt", views.robots_txt),
    path("llms.txt", views.llms_txt),
    path("sitemap.xml", sitemap, {"sitemaps": {"pages": views.AllLocalesSitemap}}),
    path("feed/", views.PostsFeed()),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]
