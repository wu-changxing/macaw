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
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    # path('add-recommendation-code/', views.add_recommendation_code, name='add_recommendation_code'),
    path('create-user/', views.create_user, name='create_user'),
    path('', views.eac, name='eac'),  # b
    path('*args', views.eac, name='eac'),  # b

]
urlpatterns = format_suffix_patterns(urlpatterns)
