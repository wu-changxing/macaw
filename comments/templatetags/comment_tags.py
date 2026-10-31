from django import template

from ..views import MESSAGE

register = template.Library()


@register.inclusion_tag("comments/comments.html", takes_context=True)
def page_comments(context, page):
    return {
        "page": page,
        "comments": page.wallet_comments.filter(is_visible=True),
        "message_template": MESSAGE,
        "request": context["request"],
    }
