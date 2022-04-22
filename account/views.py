from django.shortcuts import render, redirect, reverse
from django.urls import resolve
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from .forms import RegistrationForm, AccountAuthenticationForm, AccountUpdateForm
from django.http import HttpResponse
from .models import Account
from public_chat.models import PublicChatRoom
from django.contrib.auth.decorators import login_required


@login_required(login_url='login')
def chat(request):
    return render(request, 'account/inbox.html')


def register_view(request):
    context = {}
    form = RegistrationForm()
    context['form'] = form
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email').lower()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return redirect('home')
        else:
            context['form'] = form
            return render(request, 'account/register.html', context)
    return render(request, 'account/register.html', context)


def login_view(request):
    context = {}
    if request.method == 'POST':
        form = AccountAuthenticationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)
                return redirect('home')
            else:
                form.add_error('email', 'email or password is not correct')
        context['form'] = form

    else:
        context['form'] = AccountAuthenticationForm()
    return render(request, 'account/login.html', context)


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def info_view(request, username):
    context = {}
    account = Account.objects.get(username=username)
    if account:
        context['account'] = account
        return render(request, 'account/account_info.html', context)
    else:
        return HttpResponse('does not exists')


@login_required(login_url='login')
def edit_view(request, username):
    context = {}
    if request.user.username != username:
        return redirect('home')

    account = Account.objects.get(username=username)
    form = AccountUpdateForm(instance=request.user)
    if request.POST:
        form = AccountUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('account-info', username=account.username)
        else:
            print(form.errors)

    context['form'] = form
    context['account'] = account
    return render(request, 'account/edit.html', context)


@login_required(login_url='login')
def user_rooms(request):
    context = {}
    user = request.user
    user_owners = PublicChatRoom.objects.filter(owner=user)
    user_rooms = user.registered_users.all()

    q = user_rooms.union(user_owners)

    context['rooms'] = q
    context['domain'] = settings.BASE_DIR
    return render(request, 'account/user_rooms.html', context)



