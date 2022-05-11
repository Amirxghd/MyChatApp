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
def clear_chat_history(request, private_room_id):
    user = request.user
    try:
        room = PrivateChatRoom.objects.get(id=private_room_id)
    except PrivateChatRoom.DoesNotExist:
        return HttpResponse('this room does not exists')

    if room.user1 == user or room.user2 == user:
        try:
            messages = PrivateRoomChatMessage.objects.filter(room=room)
        except PrivateRoomChatMessage.DoesNotExist:
            return HttpResponse('this room does not exists')
        messages.delete()
    if room.user1 == request.user:
        other_user = room.user2
    else:
        other_user = room.user1

    request.session['account_id'] = other_user.id
    return redirect('chat')