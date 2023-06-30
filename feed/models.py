# feed/models.py
from django.db import models
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.api import APIField
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.documents.models import Document

class FeedPage(Page):
    subpage_types = ['feed.FeedArticlePage', 'feed.BookPage']
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

    parent_page_types = ['feed.FeedPage']

# feed/models.py

class BookPage(Page):
    introduction = models.CharField(max_length=250, blank=True)
    content = RichTextField(blank=True)
    attachment = models.ForeignKey(
        'wagtaildocs.Document', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('content', classname="full"),
        FieldPanel('attachment'),  # Changed DocumentChooserPanel to FieldPanel
    ]

    api_fields = [
        APIField('title'),
        APIField('introduction'),
        APIField('content'),
        APIField('attachment'),
    ]

    parent_page_types = ['feed.FeedPage']
