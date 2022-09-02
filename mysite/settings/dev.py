from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

WAGTAILADMIN_BASE_URL = "http://127.0.0.1"
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5#-asv=b$u6n5ac1a8orzlaoq^yevqzae%d49l%@(b93ca4_dg"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


try:
    from .local import *
except ImportError:
    pass
