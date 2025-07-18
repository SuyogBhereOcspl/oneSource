from django import forms
from django.contrib.auth.forms import AuthenticationForm,UsernameField


class LoginForm(AuthenticationForm):
    username=UsernameField(widget=forms.TextInput(attrs={"class":"form-control","autofocus":True}))
    password=forms.CharField(widget=forms.PasswordInput(attrs={"class":"form-control","autofocus":True}))

