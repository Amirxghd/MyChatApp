from django.shortcuts import render, redirect
from django.conf import settings
from PrivateChat.models import PrivateChatRoom, PrivateRoomChatMessage
from public_chat.models import PublicChatRoom
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from account.models import Account
from itertools import chain
import json

DEBUG = False

@login_required(login_url='login')
def chat_view(request, *args, **kwargs):

    context = {}
    user = request.user

    account_id = request.session.get('account_id')

    if account_id:
        try:
            other_user = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return HttpResponse('account does not exists')
        if other_user != request.user:
            room = find_or_create_private_chat(request.user, other_user)
            context['main_user'] = {
                'friend': other_user,
                'room': room
            }

    # 1. Find all the users private chats
    private_rooms1 = PrivateChatRoom.objects.filter(user1=user)
    private_rooms2 = PrivateChatRoom.objects.filter(user2=user)
    group_room1 = user.registered_users.all()
    group_room2 = PublicChatRoom.objects.filter(owner=user)

    # 2. merge the lists
    private_rooms = private_rooms1.union(private_rooms2)
    group_rooms = group_room1.union(group_room2)

    m_and_f = []
    for room in private_rooms:
        # Figure out which user is the "other user" (aka friend)
        if room.user1 == request.user:
            friend = room.user2
        else:
            friend = room.user1
        m_and_f.append({
            'friend': friend,
            'room': room,
        })
    context['m_and_f'] = m_and_f

    groups = []
    for room in group_rooms:
        groups.append({
            'message': "",
            'group': room
        })

    context['groups'] = groups

    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG
    context['username'] = request.user.username
    return render(request, "chat/chat.html", context)


def find_or_create_private_chat(user1, user2):
    try:
        chat = PrivateChatRoom.objects.get(user1=user1, user2=user2)
        return chat
    except PrivateChatRoom.DoesNotExist:
        try:
            chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
        except PrivateChatRoom.DoesNotExist:
            chat = PrivateChatRoom(user1=user1, user2=user2)
            chat.save()
        return chat
