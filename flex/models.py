"""developing page with code blocks."""
from django.db import models
from  wagtail.admin.panels import FieldPanel,StreamFieldPanel
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.core import blocks as streamfield_blocks
from wagtailcodeblock.blocks import CodeBlock
from streams import blocks
from blog.tasks.tasks import generate_image
from blog.tasks.terms import get_keywords 
from streams import blocks

class CoverForm(WagtailAdminPageForm):
    '''rewrite save function to add a step of generate wordcloud image'''
    def save(self, commit=True):
        page = super().save(commit=False)
        path ='media/' + page.title + '.png'
        content = page.content.raw_data
        body= ''
        for data in content:
            try:
                line = str(data['value'])
                body+=line
            except:
                print(data)
        if self.cleaned_data['generate_cover']:
            get_keywords.apply_async((body,),link=generate_image.s(path=path))
            self.cleaned_data['generate_cover'] = False
        page.cover_image = self.cleaned_data['title'] + '.png'
        if commit:
            page.save()
        return page

class Engineer(Page):
    """Flexible page class."""
    def get_template(self, request, *args, **kwargs):
        if request.GET.__len__() >0:
            return 'flex/tech_share.html'
        return 'flex/tech.html'
    parent_page_types = [
        'blog.BlogPage',
        'blog.BlogIndexPage',
    ]
    content = StreamField(
        [
            ("paragraph", blocks.ParagraphBlock()),
            ("quote",blocks.QuoteBlock()),
            ("poem", blocks.PoemBlock()),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
            ("cards", blocks.CardBlock()),
            ("cta", blocks.CTABlock()),
            ('codeblock',blocks.CodeStreamBlock()),
            ("button", blocks.ButtonBlock()),
            ("char_block", streamfield_blocks.CharBlock(
                required=True,
                help_text='Oh wow this is help text!!',
                min_length=10,
                max_length=50,
                template="streams/char_block.html",
            ))
        ],
        null=True,
        blank=True,
        use_json_field= True,
    )

    subtitle = models.CharField(max_length=100, null=True, blank=True)
    cover_image = models.ImageField(blank=True)
    generate_cover = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("content"),
        FieldPanel("cover_image"),
        FieldPanel("generate_cover"),
    ]

    base_form_class = CoverForm
    class Meta:  # noqa
        verbose_name = "Engineering page"
        verbose_name_plural = "Engineering Pages"









################################################################

class FlexPage(Page):
    """Flexible page class."""

    template = "flex/tech.html"
    subpage_types = ['flex.FlexPage',]
    parent_page_types = [
        'flex.FlexPage',
        'home.HomePage',
    ]
    content = StreamField(
        [
            ("title_and_text", blocks.ParagraphBlock()),
            ("full_richtext", blocks.RichtextBlock()),
            ("simple_richtext", blocks.SimpleRichtextBlock()),
            ("cards", blocks.CardBlock()),
            ("cta", blocks.CTABlock()),
            ("button", blocks.ButtonBlock()),
            ("char_block", streamfield_blocks.CharBlock(
                required=True,
                help_text='Oh wow this is help text!!',
                min_length=10,
                max_length=50,
                template="streams/char_block.html",
            ))
        ],
        null=True,
        blank=True,
        use_json_field= True,
    )

    subtitle = models.CharField(max_length=100, null=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("content"),
    ]

    class Meta:  # noqa
        verbose_name = "Flex Page"
        verbose_name_plural = "Flex Pages"
