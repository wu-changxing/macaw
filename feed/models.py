# feed/models.py
from django.db import models
from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.api import APIField  # Add this line

class ArticlePage(Page):
    content = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('content', classname="full"),
    ]

    api_fields = [  # Add this attribute
        APIField('title'),
        APIField('content'),
    ]
