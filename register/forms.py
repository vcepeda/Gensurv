from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255, required=True)
    institution = forms.CharField(max_length=255, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)  # New field for free text message

    class Meta:
        model = CustomUser
        fields = ["username", "name", "email", "institution", "password1", "password2","message"]
