# feed/api.py
from wagtail.api.v2.views import PagesAPIViewSet
from feed.models import FeedArticlePage, FeedPage, BookPage
from django.db.models import QuerySet
import random
class ArticlePageAPIViewSet(PagesAPIViewSet):
    base_page_model = FeedArticlePage

    def get_queryset(self):
        return self.base_page_model.objects.order_by('-first_published_at')[:10]


class BookPageAPIViewSet(PagesAPIViewSet):
    base_page_model = BookPage

    def get_queryset(self):
        return self.base_page_model.objects.order_by('-first_published_at')[:10]

    def serialize_page(self, page):
        # Call the superclass implementation to get the default serialized data
        data = super().serialize_page(page)

        # Add the introduction field to the serialized data
        data['introduction'] = page.introduction

        return data


class RandomArticlePageAPIViewSet(PagesAPIViewSet):
    base_page_model = FeedArticlePage

    def get_queryset(self):
        qs = self.base_page_model.objects.all().order_by('?')[:10]
        return qs

class RandomBookPageAPIViewSet(PagesAPIViewSet):
    base_page_model = BookPage

    def get_queryset(self):
        qs = self.base_page_model.objects.all().order_by('?')[:10]
        return qs