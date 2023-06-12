# subscribe/models.py
from django.db import models
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

