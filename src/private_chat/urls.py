from django.urls import path
from . import views

urlpatterns = [
    path('clear_history/<str:private_room_id>/', views.clear_chat_history, name='clear-history')
    ]