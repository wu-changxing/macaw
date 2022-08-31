from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.models import Page,Orderable
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.snippets.edit_handlers import SnippetChooserPanel




class HomeItemOrderable(Orderable):
    """This is for the pannel to choose and order items"""
    page = ParentalKey("home.HomePage", related_name="home_items")
    item = models.ForeignKey(
        "home.HomeItem",
        on_delete=models.CASCADE,
    )
    panels = [
        SnippetChooserPanel("item")
    ]


class HomeItem(models.Model):
    '''model for home items snippets'''
    name = models.CharField(max_length=200,blank=False,null=False)
    link = models.URLField(blank=True, null=True)
    intro = models.CharField(max_length=200,blank=False,null=True)
    fa = models.CharField(max_length=200,blank=False,null=True)
    panels = [
        MultiFieldPanel(
            [
                FieldPanel('name'),
                FieldPanel('link'),
                FieldPanel('intro'),
                FieldPanel('fa')
            ],
            heading = "homepage items"
        )
    ]
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Homepage Item"
        verbose_name_plural = "Homepage Items"

register_snippet(HomeItem)

class HomePage(Page):
    templates = "home/home_page.html"
    banner = models.CharField(max_length=200,blank=False,null=True)
    content_panels = Page.content_panels + [
        FieldPanel('banner'),
        MultiFieldPanel(
            [
                InlinePanel('home_items',label = 'item', min_num = 1, max_num = 12),
            ],
            heading = "Homeitems"
        )
    ]
    class Meta:
        verbose_name = "index page"