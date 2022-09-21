"""developing page with code blocks."""
from django.db import models
from  wagtail.admin.panels import FieldPanel,StreamFieldPanel
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.core import blocks as streamfield_blocks
from wagtailcodeblock.blocks import CodeBlock
from streams import blocks


class Engineer(Page):
    """Flexible page class."""

    template = "flex/tech.html"
    parent_page_types = [
        'blog.BlogPage',
        'blog.BlogIndexPage',
    ]
    content = StreamField(
        [
            ("paragraph", blocks.ParagraphBlock()),
            ("quote",blocks.QuoteBlock()),
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

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("content"),
    ]

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
