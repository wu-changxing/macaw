from django import template
from django.utils.html import format_html

from subscribe.views import new_ticket

register = template.Library()


@register.simple_tag
def human_check():
    """Hidden fields for subscribe.views.looks_human; the script fills the ticket once someone types."""
    return format_html(
        '<input type="hidden" name="ticket" value="" data-ticket="{}">'
        '<input type="text" name="website" value="" tabindex="-1" autocomplete="off" aria-hidden="true"'
        ' style="position:absolute;left:-9999px;width:1px;height:1px">'
        '<script>(function(f){{var t=f.querySelector("[data-ticket]");'
        'f.addEventListener("input",function(){{t.value=t.dataset.ticket}},{{once:true}})}})'
        '(document.currentScript.parentNode)</script>',
        new_ticket(),
    )
