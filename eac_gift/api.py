from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.images.api.fields import ImageRenditionField
from wagtail.models import Locale
from .models import Gift

class GiftViewSet(PagesAPIViewSet):
    base_queryset = Gift.objects.all()
    model = Gift  # specify the Gift model

    def get_queryset(self):
        # This will only include Gift instances for a specific locale (e.g., English)
        locale = Locale.objects.get(language_code='zh')
        return self.model.objects.filter(locale=locale)

