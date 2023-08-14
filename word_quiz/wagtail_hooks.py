from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from .models import Word

class WordSnippetViewSet(SnippetViewSet):
    model = Word
    menu_label = 'Word Quiz'
    icon = 'pilcrow'  # Updated attribute name from menu_icon to icon
    menu_order = 200
    add_to_admin_menu = True  # Added this to ensure it's displayed in the admin menu
    exclude_from_explorer = True # Added this to ensure it's displayed in the admin menu
    list_display = ('item',  'word_type', 'trans','level')  # Corrected 'cn' to 'chinese_guide'
    search_fields = ('item', 'chinese_guide')  # Corrected 'cn' to 'chinese_guide'
register_snippet(WordSnippetViewSet)
