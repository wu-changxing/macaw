# blog/serializer.py
from wagtail.api import APIField
from wagtail.api.v2.serializers import PageSerializer
from rest_framework import serializers
from wagtail.models import Page

from .author_model import BlogAuthorsOrderableSerializer
from .models import BlogPage

