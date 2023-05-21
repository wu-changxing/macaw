from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",

]
INSTALLED_APPS +=[
    "daphne",
    ]

WAGTAILADMIN_BASE_URL = "http://127.0.0.1"
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5#-asv=b$u6n5ac1a8orzlaoq^yevqzae%d49l%@(b93ca4_dg"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]
CORS_ALLOW_HEADERS = ("*")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
