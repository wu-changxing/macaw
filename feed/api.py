# feed/api.py
from wagtail.api.v2.views import PagesAPIViewSet
from feed.models import ArticlePage
from django.db.models import QuerySet
import random
class ArticlePageAPIViewSet(PagesAPIViewSet):
    base_page_model = ArticlePage

    def get_queryset(self):
        return self.base_page_model.objects.order_by('-first_published_at')[:10]
class RandomArticlePageAPIViewSet(PagesAPIViewSet):
    base_page_model = ArticlePage

    def get_queryset(self):
        qs = self.base_page_model.objects.all().order_by('?')[:10]
        return qs