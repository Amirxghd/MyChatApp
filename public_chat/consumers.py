from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.paginator import Paginator
from django.core.serializers import serialize
from datetime import datetime
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.serializers.python import Serializer

import json
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer


from public_chat.models import PublicChatRoom, PublicRoomChatMessage
from public_chat.constansts import *
from account.models import Account

User = get_user_model()


class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("PublicChatConsumer: connect: " + str(self.scope["user"]))
        # let everyone connect. But limit read/write to authenticated users
        await self.accept()
        self.room_id = None

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # leave the room
        print("PublicChatConsumer: disconnect")
        try:
            if self.room_id:
                await self.leave_room(self.room_id)
        except Exception:
            pass

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        print("PublicChatConsumer: receive_json: " + str(command))
        try:
            if command == "send":
                if len(content['message'].lstrip()) == 0:
                    raise ClientError(422, 'you can not send empty message')
                await self.send_room(content['room'], content['message'])
            elif command == 'join':
                await self.join_room(content['room'])

            elif command == 'leave':
                await self.leave_room(content['room'])
            elif command == 'get_room_chat_messages':
                await self.display_progress_bar(True)
                room = await get_room_or_error(content['room_id'])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload:
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, 'something went wrong retrieving chatroom messages')
                await self.display_progress_bar(False)
        except ClientError as e:
            await self.handle_client_error(e)
            await self.display_progress_bar(False)

    async def send_room(self, room_id, message):

        print("publicChatConsumer: send_room")

        if self.room_id:
            if str(room_id) != str(self.room_id):
                raise ClientError("ROOM_ACCESS DENIED", "room access denied")
            if not is_authenticated(self.scope['user']):
                raise ClientError("AUTH ERROR", "AUTH error")
        else:
            raise ClientError("ROOM_ACCESS DENIED", "room access denied")

        room = await get_room_or_error(room_id)
        await create_public_room_chat_message(room, self.scope['user'], message)

        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "profile_image": self.scope['user'].profile_image.url,
                "username": self.scope['user'].username,
                "user_id": self.scope['user'].id,
                "content": message,
            }
        )

    async def chat_message(self, event):
        print("public chatConsumer: chat message from user #" + str(event['user_id']))
        timestamp = calculate_timestamp(timezone.now())

        await self.send_json(
            {
            "msg_type": MSG_TYPE_MESSAGE,
            "profile_image": event['profile_image'],
            "username": event['username'],
            "user_id": event['profile_image'],
            "content": event['content'],
            "timestamp": timestamp,
            }
        )

    async def join_room(self, room_id):
        # Called by the receive_json when someone sent a JOIN command
        print("public chat consumer : join _room")

        is_auth = is_authenticated(self.scope['user'])
        try:
            room = await get_room_or_error(room_id)
        except ClientError as e:
            await self.handle_client_error(e)

        # Add user to 'user' list for the room
        if is_auth:
            await connect_user(room, self.scope['user'])

        await is_user_registered_in_room(room, self.scope['user'])

        self.room_id = room.id

        # Add them to group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )
        # tell the client to finish opening the room
        await self.send_json({
            "join": str(room.id)
        })

        # Notify the group that someone joined
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.join",
                "room_id": room_id,
                "profile_image": self.scope["user"].profile_image.url,
                "username": self.scope["user"].username,
                "user_id": self.scope["user"].id,
            }
        )

    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        print("Private Consumer: chat_join: " + str(self.scope["user"].id))
        if event["username"]:
            await self.send_json(
                {
                    "msg_type": MSG_TYPE_ENTER,
                    "room": event["room_id"],
                    "profile_image": event["profile_image"],
                    "username": event["username"],
                    "user_id": event["user_id"],
                    "content": event["username"] + " connected.",
                },
            )

    async def leave_room(self, room_id):
        # Called by the receive_json when someone sent a LEAVE command

        print('Publich chat consumer: leave room')

        is_auth = is_authenticated(self.scope['user'])

        room = await get_room_or_error(room_id)

        # remove user from 'users' room

        if is_auth:
            await disconnect_user(room, self.scope['user'])

        self.room_id = None

        # remove from the group so the dont receive messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name
        )
        # Notify the group that someone left
        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.leave",
                "room_id": room_id,
                "profile_image": self.scope["user"].profile_image.url,
                "username": self.scope["user"].username,
                "user_id": self.scope["user"].id,
            }
        )

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        print("Private Consumer: chat_leave- ", event["username"])
        if event["username"]:
            await self.send_json(
            {
                "msg_type": MSG_TYPE_LEAVE,
                "room": event["room_id"],
                "profile_image": event["profile_image"],
                "username": event["username"],
                "user_id": event["user_id"],
                "content": event["username"] + " disconnected.",
            },
        )



    async def send_messages_payload(self, messages, new_page_number):
        # Send a payload of messages to the UI
        print("public chat consumer :send messages payload")
        await self.send_json(
            {
                "messages_payload": "messages_payload",
                "messages": messages,
                "new_page_number": new_page_number,
            }
        )

    async def handle_client_error(self, e):
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
        await self.send_json(errorData)

    async def display_progress_bar(self, is_display):
        print("display progress bar")
        await self.send_json({
            "display_progress_bar": is_display
        })

    async def connected_user_count(self, event):
        print("PublicChatConsumer: connect_user_count: " + str(event['connected_user_count']))
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USER_COUNT,
            "connected_user_count": event["connected_user_count"]

        })

    ## my Code ##
    async def connected_users(self, event):
        print("PublicChatConsumer: connect_user_count" + str(event['connected_users']))
        await self.send_json({
            "msg_type": MSG_TYPE_CONNECTED_USERS,
            "connected_users": event["connected_users"]
        })

    ## my Code ##


@database_sync_to_async
def get_connected_users(room):
    serializer = RoomSerializer(room)
    return serializer.data


@database_sync_to_async
def get_num_connected_users(room):
    if room.users:
        return room.users.count()
    return 0


def is_authenticated(user):
    if user.is_authenticated:
        return True
    return False


@database_sync_to_async
def create_public_room_chat_message(room, user, message):
    return PublicRoomChatMessage.objects.create(room=room, user=user, content=message)


@database_sync_to_async
def connect_user(room, user):
    return room.connect_user(user)


@database_sync_to_async
def disconnect_user(room, user):
    return room.disconnect_user(user)


@database_sync_to_async
def get_room_or_error(room_id):
    try:
        room = PublicChatRoom.objects.get(id=room_id)
    except PublicChatRoom.DoesNotExist:
        raise ClientError("room invalid", "invalid room")

    return room


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PublicRoomChatMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            payload['messages'] = PublicRoomChatMessageSerializer(p.page(page_number).object_list, many=True).data
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print("EXCEPTION: " + str(e))
        return None


@database_sync_to_async
def is_user_registered_in_room(room, user):
    if user not in room.registered_users.all() and user != room.owner:
        raise ClientError("You are not registered for this Room", "You are not registered for this Room")
    return True


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['username', 'profile_image']


class PublicRoomChatMessageSerializer(serializers.ModelSerializer):
    user = AccountSerializer(many=False, read_only=True)
    msg_type = serializers.ReadOnlyField(default=MSG_TYPE_MESSAGE)
    timestamp = serializers.ReadOnlyField()
    class Meta:
        model = PublicRoomChatMessage
        fields = '__all__'

    def to_representation(self, data):
        data = super(PublicRoomChatMessageSerializer, self).to_representation(data)
        data['timestamp'] = calculate_timestamp(data.get('timestamp'))
        return data


class RoomSerializer(serializers.ModelSerializer):
    users = AccountSerializer(many=True, read_only=True)
    class Meta:
        model = PublicChatRoom
        fields = ['users']


class ClientError(Exception):
    def __init__(self, code, message):
        super(ClientError, self).__init__()
        self.code = code
        if message:
            self.message = message


def calculate_timestamp(timestamp):
    if (naturalday(timestamp) =='today') or (naturalday(timestamp) == 'yesterday'):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
    return str(ts)
