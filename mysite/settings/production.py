from .base import *

DEBUG = False
ALLOWED_HOSTS = ["aaron404.com"]
try:
    from .local import *
except ImportError:
    pass
