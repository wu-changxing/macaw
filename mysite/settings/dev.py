# mysite/settings/dev.py
from .base import *
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'socketio': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "https://eac.aaron404.com",
    "https://aaron404.com",

]


#  WAGTAILADMIN_BASE_URL = "http://0.0.0.0"
WAGTAILADMIN_BASE_URL = "https://aaron404.com"
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-5#-asv=b$u6n5ac1a8orzlaoq^yevqzae%d49l%@(b93ca4_dg"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

print('dev settings is running')

try:
    from .local import *
except ImportError:
    pass
