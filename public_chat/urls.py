from django.urls import path
from public_chat import views

urlpatterns = [
    path('group/<str:username>/', views.group_chat, name='group_chat'),
    path('create/', views.create_group, name='create_group'),
    path('join/<str:invite_link>/', views.join_to_group, name='join_group'),
    path('edit/<str:username>/', views.edit_group, name='edit_room'),
    path('remove/<str:username>/', views.remove_group, name='remove_group'),
    path('exit/<str:username>/', views.exit_group, name='exit_group'),
    path('reset_invite_link/<str:group_id>/', views.reset_invite_link, name='reset_invite_link'),
    ]