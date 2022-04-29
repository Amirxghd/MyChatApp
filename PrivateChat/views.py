from django.shortcuts import render, redirect
from django.conf import settings
from .models import PrivateChatRoom, PrivateRoomChatMessage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from account.models import Account
from itertools import chain
import json

DEBUG = False



@login_required(login_url='login')
def private_chat(request, *args, **kwargs):

    context = {}
    account_id = request.POST.get('account_id')

    if account_id:
        try:
            other_user = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return HttpResponse('account does not exists')

        new_room = find_or_create_private_chat(request.user, other_user)
        context['main_user'] = other_user


    # 1. Find all the rooms this user is a part of
    rooms1 = PrivateChatRoom.objects.filter(user1=request.user)
    rooms2 = PrivateChatRoom.objects.filter(user2=request.user)

    # 2. merge the lists
    rooms = list(chain(rooms1, rooms2))

    """
    m_and_f:
        [{"message": "hey", "friend": "Mitch"}, {"message": "You there?", "friend": "Blake"},]
    Where message = The most recent message
    """
    m_and_f = []
    for room in rooms:
        # Figure out which user is the "other user" (aka friend)
        if room.user1 == request.user:
            friend = room.user2
        else:
            friend = room.user1
        m_and_f.append({
            'message': "", # blank msg for now (since we have no messages)
            'friend': friend
        })
    context['m_and_f'] = m_and_f

    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG
    context['username'] = request.user.username
    return render(request, "PrivateChat/private_chat.html", context)


# Ajax call to return a private chatroom or create one if does not exist
def create_or_return_private_chat(request, *args, **kwargs):
    user1 = request.user
    payload = {}
    if user1.is_authenticated:
        if request.method == "POST":
            user2_id = request.POST.get("user2_id")
            try:
                user2 = Account.objects.get(pk=user2_id)
                chat = find_or_create_private_chat(user1, user2)
                payload['response'] = "Successfully got the chat."
                payload['chatroom_id'] = chat.id
            except Account.DoesNotExist:
                payload['response'] = "Unable to start a chat with that user."
    else:
        payload['response'] = "You can't start a chat if you are not authenticated."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def find_or_create_private_chat(user1, user2):
    try:
        chat = PrivateChatRoom.objects.get(user1=user1, user2=user2)
    except PrivateChatRoom.DoesNotExist:
        try:
            chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
        except PrivateChatRoom.DoesNotExist:
            chat = PrivateChatRoom(user1=user1, user2=user2)
            chat.save()
    return chat