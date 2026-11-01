from django.db import models
from wagtail.models import Page


class Comment(models.Model):
    """A reader comment whose author proved wallet ownership by signing it."""

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="wallet_comments")
    address = models.CharField(max_length=42, db_index=True)
    body = models.TextField(max_length=2000)
    issued_at = models.DateTimeField()
    signature = models.CharField(max_length=132)
    intent = models.CharField(max_length=64, unique=True, help_text="sha256 of signer + signed message")
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.short_address}: {self.body[:40]}"

    @property
    def short_address(self):
        return f"{self.address[:6]}…{self.address[-4:]}"
