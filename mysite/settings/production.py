# mysite/settings/production.py
# -*- coding: utf-8 -*-
from .base import *
from .secret import *
import os
WAGTAILADMIN_BASE_URL = "https://aaron404.com"
# # WAGTAILADMIN_BASE_URL = "0.0.0.0"
# CSRF_TRUSTED_ORIGINS = ['https://aaron404.com',]
#
# DEBUG = True
# ALLOWED_HOSTS = ["aaron404.com", "localhost", ]
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS = [
#     "https://eac.aaron404.com",
#     "https://aaron404.com",
# ]
#
print('production settings is running')
try:
    SECRET_KEY = DJANGO_SECRET_KEY
except:
    print('cant import secret')
