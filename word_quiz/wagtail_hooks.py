from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from .models import Word

class WordAdmin(ModelAdmin):
    model = Word
    menu_label = 'Word Quiz'  # Display name in the Wagtail admin menu
    menu_icon = 'pilcrow'  # Icon from http://fontawesome.io used for the menu item
    menu_order = 200  # Defines the position in the menu
    add_to_settings_menu = False  # Whether it should be added to the settings menu
    exclude_from_explorer = False  # Whether it should be excluded from the explorer menu
    list_display = ('item', 'usphone', 'ukphone', 'cn')  # Columns to display in the listing
    search_fields = ('item', 'cn')  # Fields to search by in the listing

modeladmin_register(WordAdmin)
