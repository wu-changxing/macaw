from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_address", "body", "page", "is_visible", "created_at")
    list_filter = ("is_visible",)
    list_editable = ("is_visible",)
    search_fields = ("address", "body")
    readonly_fields = ("page", "address", "body", "issued_at", "signature", "created_at")
