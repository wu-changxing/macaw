from django.db import models
from wagtail.api import APIField
from wagtail.models import Page
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.images.api.fields import ImageRenditionField

class GiftIndex(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]


class Gift(Page):
    name = models.CharField(max_length=255)
    description = RichTextField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    credits = models.DecimalField(max_digits=10, decimal_places=2)
    exp = models.IntegerField()
    designer = models.CharField(max_length=255)
    content_panels = Page.content_panels + [
        FieldPanel('name'),
        FieldPanel('image'),
        FieldPanel('credits'),
        FieldPanel('exp'),
        FieldPanel('designer'),
        FieldPanel('description', classname="full"),
    ]

    parent_page_types = [
        'eac_gift.GiftIndex',
    ]


    api_fields = [
    APIField('name'),
    APIField('description'),
    # APIField('image', serializer=ImageRenditionField('fill-500x500')),
        APIField('image', serializer=ImageRenditionField('original')),
    APIField('credits'),
    APIField('exp'),
    APIField('designer'),
    ]
