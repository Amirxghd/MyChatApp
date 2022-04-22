from django.urls import path
from . import views

urlpatterns = [
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('info/<str:username>/', views.info_view, name='account-info'),
    path('edit/<str:username>/', views.edit_view, name='edit-account'),
    path('user_rooms/', views.user_rooms, name='user_rooms'),
]