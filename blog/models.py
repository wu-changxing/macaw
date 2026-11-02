# blog/models.py
from uuid import uuid4

from django.core.paginator import Paginator
from django.db import models, transaction
from wagtail.api import APIField
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.api.v2.serializers import PageSerializer
from wagtail.fields import RichTextField
from wagtail.admin.panels import (
    FieldPanel,
    MultiFieldPanel,
    InlinePanel,
)
from rest_framework import serializers
from wagtail.models import Page
from wagtail.signals import page_published
from wagtail.search import index
from wagtail.admin.panels import FieldPanel
from .tasks.tasks import generate_keywords_and_image  # Updated import
from .tasks.send_email import send_emails
from .author_model import BlogAuthorsOrderableSerializer, BlogAuthorsOrderable, BlogAuthor
from subscribe.models import Subscriber


class CoverForm(WagtailAdminPageForm):
    '''rewrite save function to add a step of generating a wordcloud image'''

    def save(self, commit=True):
        is_new = self.instance.pk is None
        page = super().save(commit=False)
        body = page.body

        if self.cleaned_data['generate_cover']:
            # Using the combined task here
            filename = f'covers/{uuid4().hex}.png'
            generate_keywords_and_image.delay(body, filename)
            page.generate_cover = False
            self.cleaned_data['generate_cover'] = False
            page.cover_image = filename

        # notify_subscribers is acted on at publish time, see notify_on_publish.
        if commit:
            page.save()

        return page


class BlogPage(Page):
    def get_template(self, request, *args, **kwargs):
        if request.GET.get('type') == 'share':
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
        from flex.models import Engineer

        context = super().get_context(request, *args, **kwargs)
        context["previous_page"] = self.get_prev_siblings().live().public().type(BlogPage, Engineer).first()
        context["next_page"] = self.get_next_siblings().live().public().type(BlogPage, Engineer).first()
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
        APIField('children', serializer=ChildPagesSerializer(source='public_posts', many=True, read_only=True))
    ]

    def public_posts(self):
        """Published, public article children (the API must not list drafts or restricted pages)."""
        from flex.models import Engineer  # flex imports blog, so import here
        return self.get_children().live().public().type(BlogPage, Engineer).specific()

    def get_context(self, request, *args, **kwargs):
        """Adding custom stuff to our context."""
        context = super().get_context(request, *args, **kwargs)
        posts = self.public_posts().order_by("-first_published_at", "-pk")
        context["posts"] = Paginator(posts, 12).get_page(request.GET.get("page"))
        return context


def notify_on_publish(sender, instance, revision=None, **kwargs):
    """Send the newsletter when a flagged article is published (never on draft save), only if public.

    The flag is cleared on the page and its published revision so re-publishing doesn't mail twice.
    """
    if not instance.notify_subscribers:
        return
    type(instance).objects.filter(pk=instance.pk).update(notify_subscribers=False)
    if revision is not None:
        revision.content["notify_subscribers"] = False
        revision.save(update_fields=["content"])
    if not Page.objects.public().filter(pk=instance.pk).exists():
        return
    image_url = instance.cover_image.url if instance.cover_image else None
    transaction.on_commit(lambda: send_emails.delay(instance.title, instance.get_url(), image_url))


page_published.connect(notify_on_publish, sender=BlogPage)
