# blog/models.py
from django.db import models
from django.template.loader import render_to_string
from wagtail.api import APIField
# import geocoder  # not in Wagtail, for example only - https://geocoder.readthedocs.io/
from wagtail.admin.forms import WagtailAdminPageForm
from modelcluster.fields import ParentalKey
from wagtail.api.v2.serializers import PageSerializer
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
)
from rest_framework import serializers
from wagtail.models import Page
import segno
from wagtail import blocks as streamfield_blocks
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel
from .tasks.tasks import generate_image
from .tasks.terms import get_keywords
from .tasks.send_email import send_emails  # Add this import
from streams import blocks
from .author_model import BlogAuthorsOrderableSerializer, BlogAuthorsOrderable, BlogAuthor
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from subscribe.models import Subscriber

import re


class CoverForm(WagtailAdminPageForm):
    '''rewrite save function to add a step of generate wordcloud image'''

    def save(self, commit=True):
        is_new = self.instance.pk is None
        page = super().save(commit=False)
        path = 'media/' + page.title + '.png'
        body = page.body
        if self.cleaned_data['generate_cover']:
            get_keywords.apply_async((body,), link=generate_image.s(path=path))
            self.cleaned_data['generate_cover'] = False
            page.cover_image = self.cleaned_data['title'] + '.png'
        if self.cleaned_data.get('notify_subscribers', False):
            page.notify_subscribers = False
            self.cleaned_data['notify_subscribers'] = False
            # Fetch all subscriber emails
            subscriber_emails = list(Subscriber.objects.values_list('email', flat=True))
            # subscriber_emails = ['yingxiaohao@outlook.com']
            image_url = page.cover_image.url if page.cover_image else None
            qr_code_path = 'static/email' + page.title.replace(' ', '_') + '_qr.gif'
            # call send_emails task here
            send_emails.delay(page.title, page.get_url(), image_url, qr_code_path, subscriber_emails)
        if commit:
            page.save()

        return page



class BlogPage(Page):
    def get_template(self, request, *args, **kwargs):
        if request.GET.__len__() > 0:
            return 'blog/blog_share.html'
        return 'blog/blog_page.html'

    date = models.DateField("Post date")
    body = RichTextField(blank=True)
    generate_cover = models.BooleanField(default=False)
    cover_image = models.ImageField(blank=True)
    notify_subscribers = models.BooleanField(default=False)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('date'),
    ]
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        MultiFieldPanel(
            [
                InlinePanel("blog_authors", label="Author",
                            min_num=1, max_num=5)
            ],
            heading="Author(s)"
        ),
        FieldPanel('body', classname="full"),
        FieldPanel('generate_cover'),
        FieldPanel('cover_image'),
        FieldPanel('notify_subscribers'),

    ]
    api_fields = [
        APIField('body'),
        APIField('date'),
        APIField('blog_authors',
                 serializer=BlogAuthorsOrderableSerializer(many=True)),
    ]

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        count = len(self.get_siblings())
        prev_count = len(self.get_prev_siblings())
        next_count = len(self.get_next_siblings())
        prev_p = int((prev_count / count * 10) / 2)
        next_p = int((next_count / count * 10) / 2)
        if next_p + prev_p < 6:
            next_p += 1
            prev_p += 1
        context["prev_p"] = '<' * int(prev_p)
        context["next_p"] = '>' * int(next_p)
        return context

    base_form_class = CoverForm


class ChildPagesSerializer(PageSerializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    date = serializers.DateField(source='specific.date')
    html_url = serializers.URLField(source='url')
    detail_url = serializers.URLField(source='url')
    type = serializers.CharField(source='content_type.model')
    cover_image = serializers.ImageField(source='specific.cover_image')

    class Meta:
        model = BlogPage
        fields = ['id', 'title', 'html_url', 'detail_url', 'date', 'type', 'cover_image']

    meta_fields = ['type', 'detail_url', 'html_url', 'slug', 'show_in_menus', 'seo_title', 'search_description',
                   'first_published_at', 'parent']


class BlogIndexPage(Page):
    template = "blog/post_index.html"
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full")
    ]

    api_fields = [
        APIField('intro'),
        APIField('children', serializer=ChildPagesSerializer(source='get_children', many=True, read_only=True))
    ]

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        context["posts"] = self.get_children().public().live()
        return context
