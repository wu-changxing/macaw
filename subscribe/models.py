# subscribe/models.py
import secrets

from django.conf import settings
from django.db import models
from django.urls import reverse


def new_token():
    return secrets.token_urlsafe(32)


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=255, blank=True,
                                default="anonymous")  # Default name set to 'anonymous' Added field, blank=True allows the field to be optional
    client_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Double opt-in: only confirmed rows receive the newsletter.
    confirmed = models.BooleanField(default=False)
    # Secret in the confirm and unsubscribe links.
    token = models.CharField(max_length=64, unique=True, default=new_token)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)

    def link(self, name):
        # Absolute URL for 'confirm' or 'unsubscribe'; emails need the full site address.
        return settings.WAGTAILADMIN_BASE_URL + reverse(f'subscribe:{name}', args=[self.token])

    def __str__(self):
        return f"{self.nickname} <{self.email}>" if self.nickname else self.email
