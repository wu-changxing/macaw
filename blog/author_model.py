# blog/authors_model.py
from modelcluster.fields import ParentalKey
from wagtail.models import Page, Orderable
from rest_framework import serializers
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.db import models
from wagtail.snippets.models import register_snippet


class BlogAuthorsOrderable(Orderable):
    """This allows us to select one or more blog authors from Snippets."""

    page = ParentalKey("blog.BlogPage", related_name="blog_authors")
    author = models.ForeignKey(
        "blog.BlogAuthor",
        on_delete=models.CASCADE,
    )
    panels = [
        FieldPanel("author"),
    ]


class BlogAuthorsOrderableSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name')

    class Meta:
        model = BlogAuthorsOrderable
        fields = ['author_name']

@register_snippet
class BlogAuthor(models.Model):
    '''Modelfor snippet'''
    name = models.CharField(max_length=100, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    panels = [
        MultiFieldPanel(
            [
                FieldPanel('name'),
                FieldPanel("website"),
                FieldPanel("image")
            ],
            heading="name & image"

        )
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"

