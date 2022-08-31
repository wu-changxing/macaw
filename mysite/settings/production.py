from .base import *
from .secret import *
import os


DEBUG = False
ALLOWED_HOSTS = ["aaron404.com"]

try:
    SECRET_KEY  = DJANGO_SECRET_KEY
    # SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
except:
    print('cant import secret')
