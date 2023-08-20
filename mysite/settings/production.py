# mysite/settings/production.py
# -*- coding: utf-8 -*-
from .base import *
from .secret import *
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'socketio': {  # New logger for Socket.IO
            'handlers': ['file'],
            'level': 'ERROR',  # Set level to ERROR
            'propagate': False,
        },
    },
}
WAGTAILADMIN_BASE_URL = "https://aaron404.com"
# # WAGTAILADMIN_BASE_URL = "0.0.0.0"
CSRF_TRUSTED_ORIGINS = ['https://aaron404.com']

DEBUG = False
# DEBUG = True
ALLOWED_HOSTS = ["aaron404.com", "localhost", "127.0.0.1"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://eac.aaron404.com",
    "https://aaron404.com",
    "https://gpt.aaron404.com",
    "https://blog.aaron404.com",
]

print('production settings is running')
try:
    SECRET_KEY = DJANGO_SECRET_KEY
except:
    print('cant import secret')
