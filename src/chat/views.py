from django.shortcuts import render
from django.conf import settings
from private_chat.models import PrivateChatRoom
from public_chat.models import PublicChatRoom
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from account.models import Account
from django.db.models import Q

DEBUG = False


@login_required(login_url='login')
def chat_view(request, *args, **kwargs):

    context = {}
    user = request.user

    account_id = request.POST.get('account_id')
    if not account_id:
        account_id = request.session.get('account_id')

    if account_id:
        try:
            other_user = Account.objects.get(id=account_id)
        except Account.DoesNotExist:
            return HttpResponse('account does not exists')
        if other_user != request.user:
            room = find_or_create_private_chat(request.user, other_user)
            context['start_upp_user'] = {
                'friend': other_user,
                'room': room
            }

    group_id = request.session.get('group_id')
    if group_id:
        try:
            room = PublicChatRoom.objects.get(id=group_id)
        except PublicChatRoom.DoesNotExist:
            return HttpResponse('Group does not exists')

        context['start_upp_group'] = {
            'room': room
        }

    search_query = request.POST.get('q-chat')

    private_rooms1 = PrivateChatRoom.objects.filter(user1=user)
    private_rooms2 = PrivateChatRoom.objects.filter(user2=user)


    group_room1 = user.registered_users.all()
    group_room2 = PublicChatRoom.objects.filter(owner=user)

    if search_query:
        # 1. Find all the users private chats

        private_rooms1 = private_rooms1.filter(user2__username__icontains=search_query)
        private_rooms2 = private_rooms2.filter(user1__username__icontains=search_query)

        group_room1 = group_room1.filter(Q(chat_username__icontains=search_query)|Q(title__icontains=search_query))
        group_room2 = group_room2.filter(Q(chat_username__icontains=search_query)|Q(title__icontains=search_query))

        context['search_query'] = search_query

    # 2. merge the lists
    private_rooms = private_rooms1.union(private_rooms2)
    group_rooms = group_room1.union(group_room2)

    privates = []
    for room in private_rooms:
        # Figure out which user is the "other user" (aka friend)
        if room.user1 == request.user:
            friend = room.user2
        else:
            friend = room.user1
        privates.append({
            'friend': friend,
            'room': room,
        })
    context['privates'] = privates

    groups = []
    for room in group_rooms:
        groups.append({
            'group': room
        })

    context['groups'] = groups

    context['debug'] = DEBUG
    context['debug_mode'] = settings.DEBUG
    context['username'] = user.username
    context['auth_user'] = user
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
