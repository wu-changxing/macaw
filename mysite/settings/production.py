from .base import *
from .secret import *
import os
WAGTAILADMIN_BASE_URL = "https://aaron404.com"
# WAGTAILADMIN_BASE_URL = "0.0.0.0"

# DEBUG = False
ALLOWED_HOSTS = ["aaron404.com"]
DEBUG = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://eac.aaron404.com",
    "https://aaron404.com",

]
print('production settings is running')
try:
    SECRET_KEY  = DJANGO_SECRET_KEY
except:
    print('cant import secret')
