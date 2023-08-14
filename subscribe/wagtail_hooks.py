# subscribe/wagtail_hooks.py
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Subscriber

class SubscriberSnippetViewSet(SnippetViewSet):
    model = Subscriber
    menu_label = 'Subscribers'
    menu_icon = 'pick'
    menu_order = 200
    add_to_admin_menu = True  # Added this to ensure it's displayed in the admin menu
    exclude_from_explorer =True
    list_display = ('email', 'created_at')
    search_fields = ('email',)

register_snippet(SubscriberSnippetViewSet)
