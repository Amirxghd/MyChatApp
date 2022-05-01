from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime
from django.contrib.humanize.templatetags.humanize import naturalday

from rest_framework import serializers

import json
import time

from PrivateChat.models import PrivateRoomChatMessage, PrivateChatRoom
from account.models import Account
from PrivateChat.constansts import *


class PrivateChatConsumer(AsyncJsonWebsocketConsumer):


    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("Private Consumer: connect: " + str(self.scope["user"]))

        # let everyone connect. But limit read/write to authenticated users
        await self.accept()

        # the room_id will define what it means to be "connected". If it is not None, then the user is connected.
        self.room_id = None


    async def receive_json(self, content, **kwargs) :
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        print("Private Consumer: receive_json")
        command = content.get("command", None)
        try:
            if command == "join":
                print("joining room: " + str(content['room']))
                await self.join_room(content["room"])
            elif command == "leave":
                # Leave the room
                await self.leave_room(content["room"])
            elif command == "send":
                if len(content["message"].lstrip()) == 0:
                    raise ClientError(422, "You can't send an empty message.")
                await self.send_room(content["room"], content["message"])
            elif command == "get_room_chat_messages":
                room = await get_room_or_error(content['room_id'], self.scope["user"])
                payload = await get_room_chat_messages(room, content['page_number'])
                if payload:
                    print(payload)
                    payload = json.loads(payload)
                    await self.send_messages_payload(payload['messages'], payload['new_page_number'])
                else:
                    raise ClientError(204, "Something went wrong retrieving the chatroom messages.")
            elif command == "get_user_info":
                room = await get_room_or_error(content['room_id'], self.scope["user"])
                payload = await get_user_info(room, self.scope["user"])
                if payload:
                    payload = json.loads(payload)
                    await self.send_user_info_payload(payload['user_info'])
                else:
                    raise ClientError(204, "Something went wrong retrieving the other users account details.")
        except ClientError as e:
            await self.handle_client_error(e)

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the room
        print("ChatConsumer: disconnect")
        try:
            if self.room_id:
                await self.leave_room(self.room_id)
        except Exception as e:
            print("EXCEPTION: " + str(e))
            pass

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
        print("Private Consumer: join_room: " + str(room_id))
        try:
            room = await get_room_or_error(room_id, self.scope["user"])
        except ClientError as e:
            return await self.handle_client_error(e)

        # Store that we're in the room
        self.room_id = room.id

        # Add them to the group so they get room messages
        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name,
        )

        # Instruct their client to finish opening the room
        await self.send_json({
            "join": str(room.id),
        })

        if self.scope["user"].is_authenticated:
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

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
        print("Private Consumer: leave_room")

        room = await get_room_or_error(room_id, self.scope["user"])

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

        # Remove that we're in the room
        self.room_id = None

        # Remove them from the group so they no longer get room messages
        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name,
        )
        # Instruct their client to finish closing the room
        await self.send_json({
            "leave": str(room.id),
        })

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        print("Private Consumer: send_room")
        # Check they are in this room
        if self.room_id:
            if str(room_id) != str(self.room_id):
                print("CLIENT ERRROR 1")
                raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")
        else:
            print("CLIENT ERRROR 2")
            raise ClientError("ROOM_ACCESS_DENIED", "Room access denied")

        # Get the room and send to the group about it
        room = await get_room_or_error(room_id, self.scope["user"])

        await create_room_chat_message(room, self.scope["user"], message)

        await self.channel_layer.group_send(
            room.group_name,
            {
                "type": "chat.message",
                "profile_image": self.scope["user"].profile_image.url,
                "username": self.scope["user"].username,
                "user_id": self.scope["user"].id,
                "content": message,
            }
        )

    # These helper methods are named by the types we send - so chat.join becomes chat_join
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


    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        # Send a message down to the client
        print("Private Consumer: chat_message")

        timestamp = calculate_timestamp(timezone.now())

        await self.send_json(
            {
                "msg_type": MSG_TYPE_MESSAGE,
                "username": event["username"],
                "user_id": event["user_id"],
                "profile_image": event["profile_image"],
                "content": event["content"],
                "timestamp": timestamp,
            },
        )

    async def send_messages_payload(self, messages, new_page_number):
        """
        Send a payload of messages to the ui
        """
        print("Private Consumer: send_messages_payload. ")

        await self.send_json(
            {
                "messages_payload": "messages_payload",
                "messages": messages,
                "new_page_number": new_page_number,
            },
        )

    async def send_user_info_payload(self, user_info):
        """
        Send a payload of user information to the ui
        """
        print("Private Consumer: send_user_info_payload. ")
        await self.send_json(
            {
                "user_info": user_info,
            },
        )

    async def display_progress_bar(self, is_displayed):
        """
        1. is_displayed = True
        - Display the progress bar on UI
        2. is_displayed = False
        - Hide the progress bar on UI
        """
        print("DISPLAY PROGRESS BAR: " + str(is_displayed))
        await self.send_json(
            {
                "display_progress_bar": is_displayed
            }
        )

    async def handle_client_error(self, e):
        """
        Called when a ClientError is raised.
        Sends error data to UI.
        """
        errorData = {}
        errorData['error'] = e.code
        if e.message:
            errorData['message'] = e.message
            await self.send_json(errorData)
        return


@database_sync_to_async
def get_room_or_error(room_id, user):
    """
    Tries to fetch a room for the user, checking permissions along the way.
    """
    try:
        print(room_id, user)
        room = PrivateChatRoom.objects.get(pk=room_id)
    except PrivateChatRoom.DoesNotExist:
        raise ClientError("ROOM_INVALID", "Invalid room.")

    # Is this user allowed in the room? (must be user1 or user2)
    if user != room.user1 and user != room.user2:
        raise ClientError("ROOM_ACCESS_DENIED", "You do not have permission to join this room.")

    return room


@database_sync_to_async
def get_user_info(room, user):
    """
    Retrieve the user info for the user you are chatting with
    """
    try:
        # Determine who is who
        other_user = room.user1
        if other_user == user:
            other_user = room.user2

        payload = {}
        payload['user_info'] = AccountSerializer(other_user).data
        print(payload['user_info'])
        return json.dumps(payload)
    except ClientError as e:
        raise ClientError("DATA_ERROR", "Unable to get that users information.")
    return None


@database_sync_to_async
def create_room_chat_message(room, user, message):
    return PrivateRoomChatMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = PrivateRoomChatMessage.objects.by_room(room)
        p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

        payload = {}
        new_page_number = int(page_number)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            # s = LazyRoomChatMessageEncoder()
            # payload['messages'] = s.serialize(p.page(page_number).object_list)
            z = p.page(page_number).object_list
            x = PrivateRoomChatMessageSerializer(z, many=True).data
            payload['messages'] = x
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print("EXCEPTION: " + str(e))
    return None


def calculate_timestamp(timestamp):
    if (naturalday(timestamp) =='today') or (naturalday(timestamp) == 'yesterday'):
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        str_time = str_time.strip("0")
        ts = f"{naturalday(timestamp)} at {str_time}"
    else:
        str_time = datetime.strftime(timestamp, "%m/%d/%Y")
        ts = f"{str_time}"
    return str(ts)


class ClientError(Exception):
    def __init__(self, code, message):
        super(ClientError, self).__init__()
        self.code = code
        if message:
            self.message = message


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'username', 'profile_image']


class PrivateRoomChatMessageSerializer(serializers.ModelSerializer):
    user = AccountSerializer(many=False, read_only=True)
    msg_type = serializers.ReadOnlyField(default=MSG_TYPE_MESSAGE)
    timestamp = serializers.ReadOnlyField()
    class Meta:
        model = PrivateRoomChatMessage
        fields = '__all__'

    def to_representation(self, data):
        data = super(PrivateRoomChatMessageSerializer, self).to_representation(data)
        data['timestamp'] = calculate_timestamp(data.get('timestamp'))
        return data





