from django.shortcuts import render,  redirect, reverse
from django.conf import settings
from .models import PublicChatRoom
from .forms import CreatePublicRoom, GroupEditForm
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages

DEBUG = False


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
            invite_url = settings.BASE_DIR + reverse('join_group', kwargs={'invite_link': invite_link})
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
    return redirect('chat')


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
def reset_invite_link(request, group_id):
    try:
        group = PublicChatRoom.objects.get(id=group_id)
        if group.owner != request.user:
            messages.add_message(request, messages.INFO, "You can't reset invite link, you are not Admin!")
            return redirect('chat')
        group.invite_link = get_random_string(48)
        group.save()
    except PublicChatRoom.DoesNotExist:
        pass
    return redirect('chat')


@login_required(login_url='login')
def remove_or_exit_group(request, group_id):
    try:
        group = PublicChatRoom.objects.get(id=group_id)
        if group.owner == request.user:
            group.delete()
        else:
            group.registered_users.remove(request.user)
    except PublicChatRoom.DoesNotExist:
        return HttpResponse('Group does not exists!')

    return redirect('chat')


@login_required(login_url='login')
def show_invite_link(request, group_id):
    try:
        group = PublicChatRoom.objects.get(id=group_id)
    except PublicChatRoom.DoesNotExist:
        return HttpResponse('Group does not exists!')

    invite_link_url = settings.BASE_DIR + group.get_absolute_url()
    messages.add_message(request, messages.INFO, invite_link_url)
    return redirect('chat')


def show_members(request, group_id):
    context = {}
    try:
        group = PublicChatRoom.objects.get(id=group_id)
    except PublicChatRoom.DoesNotExist:
        return HttpResponse('Group does not exists!')

    group_users = group.registered_users.all()
    context['users'] = group_users
    return render(request, 'public_chat/group_users.html', context)


















