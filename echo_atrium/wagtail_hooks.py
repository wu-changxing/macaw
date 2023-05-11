# echo_atrium/wagtail_hooks.py
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import Room, RoomParticipant, RecommendationCode
from django.shortcuts import render
from wagtail.contrib.modeladmin.views import IndexView
class RoomAdmin(ModelAdmin):
    model = Room

class RoomParticipantAdmin(ModelAdmin):
    model = RoomParticipant
class CustomIndexView(IndexView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recommendation_codes'] = self.queryset
        return context

class RecommendationCodeAdmin(ModelAdmin):
    model = RecommendationCode
    menu_label = 'Recommendation Codes'
    menu_icon = 'form'
    list_display = ('code', 'user', 'created_at')
    search_fields = ('code', 'user__username')
    index_view_class = CustomIndexView
modeladmin_register(RoomAdmin)
modeladmin_register(RoomParticipantAdmin)
modeladmin_register(RecommendationCodeAdmin)
