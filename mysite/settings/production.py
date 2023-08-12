# mysite/settings/production.py
# -*- coding: utf-8 -*-
from .base import *
from .secret import *
import os

# Update the Wagtail admin URL
WAGTAILADMIN_BASE_URL = "https://backend.aaron404.com"

# Update trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = ['https://backend.aaron404.com']

DEBUG = False

# Update allowed hosts
ALLOWED_HOSTS = ["backend.aaron404.com", "localhost", "127.0.0.1","eac.aaron404.com"]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False

# Update allowed CORS origins
CORS_ALLOWED_ORIGINS = [
    "https://eac.aaron404.com",
    "https://backend.aaron404.com",
    "https://gpt.aaron404.com"
]

print('production settings is running')

try:
    SECRET_KEY = DJANGO_SECRET_KEY
except:
    print('cant import secret')
