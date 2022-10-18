"""developing page with code blocks."""
from django.db import models
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
    StreamFieldPanel
)
from modelcluster.fields import ParentalKey
from wagtail.models import Page,Orderable
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.core import blocks as streamfield_blocks
from wagtail.snippets.models import register_snippet
from streams import blocks
from blog.tasks.tasks import generate_image
from blog.tasks.terms import get_keywords 
from streams import blocks

class AuthorsOrderable(Orderable):
    """This allows us to select one or more blog authors from Snippets."""

    page = ParentalKey("flex.Engineer", related_name="engineers")
    author = models.ForeignKey(
        "flex.Author",
        on_delete=models.CASCADE,
    )
    panels = [
        FieldPanel("author"),
    ]

class Author(models.Model):
    '''Modelfor snippet'''
    name = models.CharField(max_length=100,blank=True,null=True)
    website = models.URLField(blank=True,null=True)
    image = models.ForeignKey(
       "wagtailimages.Image",
        on_delete=models.CASCADE,
        null=True,blank=True
    )
    panels = [
        MultiFieldPanel(
            [
            FieldPanel('name'),
            FieldPanel("website"),
            FieldPanel("image")
            ],
            heading = "name & image"

        )
    ]
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

register_snippet(Author)

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
            ("math", streamfield_blocks.CharBlock(
                required=True,
                help_text='this is whole line for math block',
                min_length=1,
                max_length=1050,
                template="streams/char_block.html",
            ))
        ],
        null=True,
        blank=True,
        use_json_field= True,
    )

    
    date = models.DateField("Post date")
    cover_image = models.ImageField(blank=True)
    generate_cover = models.BooleanField(default=False)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        MultiFieldPanel(
            [
                InlinePanel("engineers", label="Author", min_num=1, max_num=5)
            ],
            heading="Author(s)"
        ),
        FieldPanel("content"),
        FieldPanel("cover_image"),
        FieldPanel("generate_cover"),
    ]
    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        count = len(self.get_siblings())
        prev_count = len(self.get_prev_siblings())
        next_count = len(self.get_next_siblings())
        prev_p = int((prev_count /count *10) / 2)
        next_p = int((next_count /count *10) / 2)
        if next_p + prev_p < 6:
            next_p +=1
            prev_p +=1
        context["prev_p"] = '<' * int(prev_p)
        context["next_p"] = '>' *  int(next_p)
        return context
    base_form_class = CoverForm
    class Meta:  # noqa
        verbose_name = "Engineering page"
        verbose_name_plural = "Engineering Pages"








