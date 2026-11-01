from django import template

from ..views import MESSAGE

register = template.Library()

SHOWN = 50


@register.inclusion_tag("comments/comments.html", takes_context=True)
def page_comments(context, page):
    visible = page.wallet_comments.filter(is_visible=True)
    latest = list(visible.order_by("-created_at")[:SHOWN])[::-1]
    return {
        "page": page,
        "comments": latest,
        "total": visible.count(),
        "message_template": MESSAGE,
        "request": context["request"],
    }
