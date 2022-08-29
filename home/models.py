from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel


class HomePage(Page):
    templates = "home/home_page.html"
    banner = models.CharField(max_length=200,blank=False,null=True)
    body = RichTextField(blank=True)
    first_title = models.CharField(max_length=200,blank=False,null=True)
    first_description = models.CharField(max_length=200,blank=False,null = True)



    content_panels = Page.content_panels + [
        FieldPanel('banner'),
        FieldPanel('body', classname="full"),
        FieldPanel('first_title'),
        FieldPanel('first_description'),

    ]

    class Meta:
        verbose_name = "index page"