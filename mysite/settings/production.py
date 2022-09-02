from .base import *
from .secret import *
import os

WAGTAILADMIN_BASE_URL = "https://aaron404.com"

DEBUG = False
ALLOWED_HOSTS = ["aaron404.com"]
# ALLOWED_HOSTS = ["*"]

try:
    SECRET_KEY  = DJANGO_SECRET_KEY
except:
    print('cant import secret')
