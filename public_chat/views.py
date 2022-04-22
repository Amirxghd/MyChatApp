from django.shortcuts import render,  redirect, reverse
from django.conf import settings
from .models import PublicChatRoom
from .forms import CreatePublicRoom, GroupEditForm
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

DEBUG = False


@login_required(login_url='login')
def group_chat(request, username):
    context = {'debug_mode': settings.DEBUG, 'debug': DEBUG, 'username': request.user.username}
    try:
        room = PublicChatRoom.objects.get(chat_username=username)
        if request.user in room.registered_users.all() or request.user == room.owner:
            context['room_id'] = room.id
            context['room'] = room
            return render(request, "public_chat/public_chat.html", context)
        else:
            return HttpResponse('You are not allowed to chat in this Room. (You are not registered for this group)')

    except PublicChatRoom.DoesNotExist:
        return redirect('home')


@login_required(login_url='login')
def create_group(request):
    user = request.user
    context = {}
    form = CreatePublicRoom()
    context['form'] = form
    if request.method == 'POST':
        form = CreatePublicRoom(request.POST)
        if form.is_valid():
            form.instance.owner = user
            invite_link = get_random_string(48)
            form.instance.invite_link = invite_link
            form.save()
            invite_url = 'http://127.0.0.1:8000' + reverse('join_group', kwargs={'invite_link': invite_link})
            return render(request, 'public_chat/create_room_form.html', {'invite_link': invite_url, 'room': form.instance})

    context['form'] = form

    return render(request, 'public_chat/create_room_form.html', context)


@login_required(login_url='login')
def join_to_group(request, invite_link):
    user = request.user
    context = {}
    try:
        group = PublicChatRoom.objects.get(invite_link=invite_link)
        if user not in group.registered_users.all() and user != group.owner:
            group.registered_users.add(user)
            return redirect('group_chat', username=group.chat_username)
    except PublicChatRoom.DoesNotExist:
        context['messgae'] = 'room does not exist'
    return redirect('home')


@login_required(login_url='login')
def edit_group(request, username):
    context = {}
    try:
        group = PublicChatRoom.objects.get(chat_username=username)
    except PublicChatRoom.DoesNotExist:
        return redirect('user_rooms')

    if request.user != group.owner:
        return redirect('user_rooms')
    form = GroupEditForm(instance=group, owner_id=group.owner.id)
    if request.method == 'POST':
        form = GroupEditForm(request.POST, request.FILES, instance=group, owner_id=group.owner.id)
        if form.is_valid():
            form.save()
            return redirect('user_rooms')
        else:
            print(form.errors)

    context['form'] = form
    context['group'] = group
    return render(request, 'public_chat/edit_group.html', context)


@login_required(login_url='login')
def reset_invite_link(request, username):
    try:
        group = PublicChatRoom.objects.get(chat_username=username)
        if group.owner != request.user:
            return redirect('user_rooms')
        group.invite_link = get_random_string(48)
        group.save()
    except PublicChatRoom.DoesNotExist:
        pass
    return redirect('user_rooms')




















