"""Set the root title before the shared base template renders its title block."""
from wagtail import hooks

from .templatetags.seo_tags import SITE_NAME, is_home


@hooks.register("before_serve_page")
def home_seo_title(page, request, args, kwargs):
    if is_home(page):
        page.seo_title = SITE_NAME
