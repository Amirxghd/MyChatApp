from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from .models import PublicChatRoom
from account.models import Account
from django.conf import settings
from django.core import validators


class CreatePublicRoom(forms.ModelForm):

    class Meta:
        model = PublicChatRoom
        fields = ['title', 'chat_username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['chat_username'].widget.attrs.update({'class': 'form-control'})

    def clean_chat_username(self):
        username = self.cleaned_data['chat_username']
        if PublicChatRoom.objects.filter(chat_username=username).exists():
            raise ValidationError("A Room with username '{}' already exists".format(username))
        return username


class GroupEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        owner_id = kwargs.pop('owner_id')
        super(GroupEditForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['registered_users'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['room_image'].widget.attrs.update({'class': 'form-control form-control-lg'})
        self.fields['registered_users'] = forms.ModelMultipleChoiceField(
                                        required=False,
                                        queryset=Account.objects.exclude(id=owner_id),
                                        widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = PublicChatRoom
        fields = ['title', 'room_image', 'registered_users']




