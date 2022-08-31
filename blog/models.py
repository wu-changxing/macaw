from django.db import models
from django import forms

import geocoder  # not in Wagtail, for example only - https://geocoder.readthedocs.io/
from wagtail.admin.forms import WagtailAdminPageForm
from modelcluster.fields import ParentalKey
from wagtail.models import Page,Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
    StreamFieldPanel
)
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.snippets.edit_handlers import SnippetChooserPanel


from threading import Thread

from .tasks import genetate_image,add

from wagtail import hooks


@hooks.register('after_publish_page')
def save_image(request,page):
    body = page.body
    title = request.POST['title']
    path ='media/' + title + '.png'
    
    genetate_image.delay(body,path)
    add.delay(body,path)



class BlogAuthorsOrderable(Orderable):
    """This allows us to select one or more blog authors from Snippets."""

    page = ParentalKey("blog.BlogPage", related_name="blog_authors")
    author = models.ForeignKey(
        "blog.BlogAuthor",
        on_delete=models.CASCADE,
    )

    panels = [
        SnippetChooserPanel("author"),
    ]

class BlogAuthor(models.Model):
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

register_snippet(BlogAuthor)

class CoverForm(WagtailAdminPageForm):
    def save(self, commit=True):
        page = super().save(commit=False)
        page.cover_image = self.cleaned_data['title'] + '.png'
        if commit:
            page.save()
        return page

class BlogIndexPage(Page):
    template_name = "blog/blog_index_page.html"
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]
    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        context["posts"] = BlogPage.objects.live().public()
        return context

class BlogPage(Page):
    def get_template(self, request, *args, **kwargs):
        if request.GET.__len__() >0:
            return 'blog/blog_share.html'
        return 'blog/blog_page.html'
    date = models.DateField("Post date")
    body = RichTextField(blank=True)
    generate_cover = models.BooleanField(default=False)
    cover_image = models.ImageField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('date'),
    ]
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        MultiFieldPanel(
            [
                InlinePanel("blog_authors", label="Author", min_num=1, max_num=5)
            ],
            heading="Author(s)"
        ),
        FieldPanel('body', classname="full"),
        FieldPanel('generate_cover'),
        FieldPanel('cover_image'),

    ]
    base_form_class = CoverForm
