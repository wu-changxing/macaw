# mysite/api.py
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from feed.api import ArticlePageAPIViewSet, RandomArticlePageAPIViewSet

# Create the router. "wagtailapi" is the URL namespace
api_router = WagtailAPIRouter('wagtailapi')

# Add the four endpoints using the "register_endpoint" method.
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)
api_router.register_endpoint('feeds', ArticlePageAPIViewSet)  # Add the new endpoint
api_router.register_endpoint('random-feeds', RandomArticlePageAPIViewSet)
