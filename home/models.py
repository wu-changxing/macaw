from django.conf import settings
from django.db import models
from django.utils.translation import get_language_info

from modelcluster.fields import ParentalKey
from wagtail.models import Locale, Page, Orderable
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel




@register_snippet
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



class HomeItemOrderable(Orderable):
    """This is for the pannel to choose and order items"""
    page = ParentalKey("home.HomePage", related_name="home_items")
    item = models.ForeignKey(
        "home.HomeItem",
        on_delete=models.CASCADE,
    )
    panels = [
        FieldPanel("item")
    ]
    
BLADE_SLUG = "musings"   # the blade door opens this section
SHADOW_SLUG = "blog"      # the blade's shadow opens the sci-fi section
SECTION_MIN_PAGES = 20   # a section is listed on the home page once it holds this many live pages
DOOR_NAMES = {BLADE_SLUG: "多余的沉思", SHADOW_SLUG: "回潮"}  # the Chinese names the scene gives its two main doors
PRIMARY_LANGUAGES = {"zh-hans": "中", "en": "EN", "ja": "日本語"}


def is_substantial(section):
    """thin sections (a handful of posts) stay off the home page"""
    return section.get_descendants().live().count() >= SECTION_MIN_PAGES


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

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        sections = self.sections()
        by_slug = {source.slug: page for source, page in sections}
        context.update(
            sections=[(source, page, DOOR_NAMES.get(source.slug, "")) for source, page in sections if is_substantial(source)],
            blade_page=by_slug.get(BLADE_SLUG),
            shadow_page=by_slug.get(SHADOW_SLUG),
            doors={item.name: item for item in HomeItem.objects.all()},
        )
        languages = self.languages()
        context["languages_primary"] = [lang for lang in languages if lang[0] in PRIMARY_LANGUAGES]
        context["languages_more"] = [lang for lang in languages if lang[0] not in PRIMARY_LANGUAGES]
        return context

    def sections(self):
        """(source, page) per live section of the default-locale home: the source gives the label,
        the page is its live translation in this locale, or the source when there is none."""
        source_home = self.get_translation_or_none(Locale.get_default()) or self
        return [(source, self.localized(source)) for source in source_home.get_children().live().public()]

    def localized(self, source):
        return source.get_translations(inclusive=True).live().public().filter(locale=self.locale).first() or source

    def languages(self):
        """(code, label, page, is_current) for each live translation of this home, in settings order."""
        pages = {p.locale.language_code: p for p in self.get_translations(inclusive=True).live().public().select_related("locale")}
        codes = [code for code, _ in settings.WAGTAIL_CONTENT_LANGUAGES if code in pages]
        return [(code, PRIMARY_LANGUAGES.get(code) or get_language_info(code)["name_local"], pages[code],
                 code == self.locale.language_code) for code in codes]
