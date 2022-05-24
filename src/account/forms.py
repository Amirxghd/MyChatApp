from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate
from .models import Account
from django.core import validators


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Add a valid email address.')

    class Meta:
        model = Account
        fields = ('email', 'username', 'password1', 'password2',)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(email=email)
        except Account.DoesNotExist:
            return email
        raise forms.ValidationError('Email "%s" is already in use.' % account)

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            account = Account.objects.exclude(pk=self.instance.pk).get(username=username)
        except Account.DoesNotExist:
            return username
        raise forms.ValidationError('Username "%s" is already in use.' % account)


class AccountAuthenticationForm(forms.Form):
    password = forms.CharField(label='password', widget=forms.PasswordInput)
    email = forms.EmailField(label='email', widget=forms.EmailInput,
                             validators=[validators.MaxLengthValidator(100),
                                         validators.EmailValidator])


class AccountUpdateForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = ['full_name', 'username', 'hide_email', 'profile_image', 'bio']

        widgets = {
            'hide_email': forms.CheckboxInput(attrs={
                'class': 'form-group'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['bio'].widget.attrs.update({'class': 'form-control', 'row': 5})
        self.fields['profile_image'].widget.attrs.update({'class': 'btn btn-secondary'})
        # self.fields['hide_email'].widget.attrs.update({'class': 'custom-control-input'})




