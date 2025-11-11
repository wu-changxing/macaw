# mysite/urls.py
from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.conf.urls.i18n import i18n_patterns
from search import views as search_views
from .api import api_router

# Non-i18n patterns (these will not have language prefix)
urlpatterns = [
    path("api/v2/", api_router.urls),  # API endpoints
    path('django-rq/', include('django_rq.urls')),
]

# Add admin and other core URLs
urlpatterns += [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# i18n patterns (these will have language prefix)
urlpatterns += i18n_patterns(
    path("subscribe/", include('subscribe.urls')),  # Moved here for i18n support
    path("search/", search_views.search, name="search"),
    path("", include(wagtail_urls)),
    prefix_default_language=False  # Changed to False to remove /en/ prefix
)
