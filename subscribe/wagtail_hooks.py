# subscribe/wagtail_hooks.py
from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register
)
from .models import Subscriber

class SubscriberAdmin(ModelAdmin):
    model = Subscriber
    menu_label = 'Subscribers'
    menu_icon = 'pick'
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('email', 'created_at')
    search_fields = ('email',)

modeladmin_register(SubscriberAdmin)
