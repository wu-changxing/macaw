# subscribe/urls.py
from django.urls import path
from . import views

app_name = 'subscribe'

urlpatterns = [
    path('new/', views.subscribe, name='new'), # Changed from 'subscribe/' to 'new/'
    path('success/', views.subscribe_success, name='subscribe_success'),
    path('confirm/<str:token>/', views.confirm, name='confirm'),
    path('unsubscribe/<str:token>/', views.unsubscribe, name='unsubscribe'),
]
