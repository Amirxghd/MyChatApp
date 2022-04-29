from django.urls import re_path, path

from public_chat.consumers import PublicChatConsumer
from PrivateChat.consumers import PrivateChatConsumer

websocket_urlpatterns = [
    path(r'public_chat/<str:room_id>/', PublicChatConsumer.as_asgi()),
    path(r'private_chat/<str:room_id>/', PrivateChatConsumer.as_asgi()),

]