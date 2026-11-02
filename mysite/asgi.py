"""ASGI entry point for the Django site."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings.production")

application = get_asgi_application()
