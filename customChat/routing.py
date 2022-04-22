from django.urls import re_path, path

from public_chat.consumers import PublicChatConsumer

websocket_urlpatterns = [
    path(r'public_chat/<str:room_id>/', PublicChatConsumer.as_asgi()),

]