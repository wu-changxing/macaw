from django.urls import path

from . import views

urlpatterns = [path("", views.post_comment, name="post_comment")]
