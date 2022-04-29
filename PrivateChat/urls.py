from django.urls import path
from . import views

urlpatterns = [
    path('', views.private_chat, name='private_chat'),
    path('create-or-return-private-chat/', views.create_or_return_private_chat, name='create-or-return-private-chat'),
    ]