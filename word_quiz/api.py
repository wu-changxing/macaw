# word_quiz/api.py
from wagtail.api.v2.views import PagesAPIViewSet
from .models import Word
from wagtail.models import Locale


class WordsAPIViewSet(PagesAPIViewSet):
    base_page_model = Word

    def get_queryset(self):
        locale = Locale.objects.get(language_code='zh-hans')
        qs = self.base_page_model.objects.filter(locale=locale).live().order_by('?')

        level = self.request.query_params.get('level', None)
        if level is not None:
            qs = qs.filter(level=int(level))
        return qs
