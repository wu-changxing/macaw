# word_quiz/models.py
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from django.db.models import JSONField   # change this line

class Sentence(models.Model):
    sentence = RichTextField()
    translation = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.sentence

    class Meta:
        verbose_name = "Sentence"
        verbose_name_plural = "Sentences"

class Word(Page):
    item = models.CharField(max_length=200)
    language = models.CharField(max_length=2, default='en')
    usphone = models.CharField(max_length=200,blank=True, null=True)
    ukphone = models.CharField(max_length=201,blank=True, null=True)
    ipa = models.CharField(max_length=200,blank=True, null=True)
    word_type = models.CharField(max_length=200,blank=True, null=True)
    sentences = models.ManyToManyField(Sentence,blank=True)
    root = models.CharField(max_length=200,blank=True, null=True)
    root_explanation = models.TextField(blank=True, null=True)
    chinese_guide = models.TextField(blank=True, null=True)
    related_words = models.JSONField(blank=True, null=True)
    meanings = JSONField(blank=True, null=True)   # use JSONField from django.db.models
    trans = models.CharField(max_length=200,blank=True, null=True)
    level = models.IntegerField(default=0)
    catagory = models.CharField(max_length=200, blank=True, null=True,default="CET")

    content_panels = Page.content_panels + [
        FieldPanel('item'),
        FieldPanel('trans'),
        FieldPanel('language'),
        FieldPanel('usphone'),
        FieldPanel('ukphone'),
        FieldPanel('ipa'),
        FieldPanel('word_type'),
        FieldPanel('root'),
        FieldPanel('root_explanation'),
        FieldPanel('chinese_guide'),
        FieldPanel('related_words'),
        FieldPanel('meanings'),
        FieldPanel('level'),
        FieldPanel('catagory'),
    ]

    api_fields = [
        APIField('item'),
        APIField('trans'),
        APIField('language'),
        APIField('usphone'),
        APIField('ukphone'),
        APIField('ipa'),
        APIField('word_type'),
        APIField('root'),
        APIField('root_explanation'),
        APIField('chinese_guide'),
        APIField('related_words'),
        APIField('level'),
        APIField('sentences'),
        APIField('catagory'),
    ]

