from django.urls import path
from public_chat import views

urlpatterns = [
    path('create/', views.create_group, name='create_group'),
    path('join/<str:invite_link>/', views.join_to_group, name='join_group'),
    path('edit/<str:group_id>/', views.edit_group, name='edit_room'),
    path('remove_or_exit/<str:group_id>/', views.remove_or_exit_group, name='remove_or_exit_group'),
    path('reset_invite_link/<str:group_id>/', views.reset_invite_link, name='reset_invite_link'),
    path('show_invite_link/<str:group_id>/', views.show_invite_link, name='show_invite_link'),
    path('show_memebers/<str:group_id>/', views.show_members, name='show_members'),
    ]