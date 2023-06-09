from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.conf.urls.i18n import i18n_patterns
from search import views as search_views
from .api import api_router
from echo_atrium.socketio_server import socket_app
from echo_atrium import urls as echo_atrium_urls
from echo_atrium.consumers import VoiceChatConsumer

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path('api/v2/', api_router.urls),
    path("eac/", include(echo_atrium_urls)),
    path("eac/<str:data>/", include(echo_atrium_urls)),
    path('ws/voice_chat/<str:room_id>/', VoiceChatConsumer.as_asgi()),
    path("socket.io/", socket_app),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + i18n_patterns(
    path("search/", search_views.search, name="search"),
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
)
