# feed/models.py
from django.db import models
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.api import APIField

class FeedPage(Page):
    subpage_types = ['feed.FeedArticlePage']
    def get_context(self, request):
        context = super().get_context(request)
        context['articles'] = self.get_children().specific().live()
        return context

class FeedArticlePage(Page):
    content = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('content', classname="full"),
    ]

    api_fields = [
        APIField('title'),
        APIField('content'),
    ]

    # Add this line:
    parent_page_types = ['feed.FeedPage']
