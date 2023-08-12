# subscribe/wagtail_hooks.py
from .models import Subscriber

from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

class SubscriberSnippetViewSet(SnippetViewSet):
    model = Subscriber
    menu_label = 'Subscribers'
    icon = 'pick' # Changed from menu_icon
    menu_order = 200
    add_to_settings_menu = False
    add_to_admin_menu = True  # If you want it on top-level admin menu
    exclude_from_explorer = False
    list_display = ('email', 'created_at')
    search_fields = ('email',)

register_snippet(SubscriberSnippetViewSet)

