# path : echo_atrium/urls.py
from django.urls import path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('api/login/', views.AuthTokenView.as_view(), name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),
    # path('add-recommendation-code/', views.add_recommendation_code, name='add_recommendation_code'),
    path('create-user/', views.create_user, name='create_user'),

]
urlpatterns = format_suffix_patterns(urlpatterns)
