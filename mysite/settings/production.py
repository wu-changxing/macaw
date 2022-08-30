from .base import *
import os


DEBUG = False
ALLOWED_HOSTS = ["aaron404.com"]
try:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
except:
    print('cant import secret')
try:
    from .local import *
except ImportError:
    pass
