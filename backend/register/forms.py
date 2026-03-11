from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255, required=True)
    institution = forms.CharField(max_length=255, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)  # New field for free text message

    class Meta:
        model = CustomUser
        fields = ["username", "name", "email", "institution", "password1", "password2","message"]

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
