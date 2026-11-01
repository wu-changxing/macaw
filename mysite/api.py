# mysite/api.py
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter

# Only pages are exposed. Image/document listings were unused and enumerated every upload,
# including ones attached to drafts or restricted collections.
api_router = WagtailAPIRouter('wagtailapi')
api_router.register_endpoint('pages', PagesAPIViewSet)
