# path : echo_atrium/urls.py
from django.urls import path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('api/login/', views.AuthTokenView.as_view(), name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/user-profile/', views.api_get_user_profile, name='api_user_profile'),
    path('api/token/verify/', views.verify_token, name='api_verify_token'),
    path('api/update-profile/', views.api_update_user_profile, name='api_update_user_profile'),
    path('api/get-recommendation-code/', views.api_get_recommend_code, name='api_get_recommend_code'),
    path('api/update-recommendation-code/', views.api_update_recommend_code, name='api_update_recommend_code'),
    path('api/get-invited-users/', views.api_get_invited_users, name='get-invited-users'),
    path('api/get-event/', views.api_get_event, name='api_get_event'),
    path('api/save-event/', views.api_save_event, name='api_save_event'),
    path('api/get-all-events/', views.api_get_all_events, name='api_get_all_events'),
    path('user/<str:username>/avatar/', views.get_user_avatar, name='get_user_avatar'),
    path('api/update-event/<int:event_id>/', views.api_update_event, name='api-update-event'),
    path('api/delete-event/<int:event_id>/', views.api_delete_event, name='api-delete-event'),
    path('api/user/<str:username>/events/', views.api_get_user_events, name='api_get_user_events'),
    # path('add-recommendation-code/', views.add_recommendation_code, name='add_recommendation_code'),
    path('create-user/', views.create_user, name='create_user'),
    path('*args', views.eac, name='eac'),  # b

]
urlpatterns = format_suffix_patterns(urlpatterns)
