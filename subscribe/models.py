# subscribe/models.py
from django.db import models

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    nickname = models.CharField(max_length=255, blank=True,
                                default="anonymous")  # Default name set to 'anonymous' Added field, blank=True allows the field to be optional
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nickname} <{self.email}>" if self.nickname else self.email


