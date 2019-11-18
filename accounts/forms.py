from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

user_model = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = [
            'username', 'email', 'password1', 'password2'
        ]

    def clean_email(self):
        if User.objects.filter(email=self.cleaned_data.get('email')).exists():
            raise forms.ValidationError('This email exists on system')
        return self.cleaned_data['email']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.email = self.cleaned_data.get('email')
            user.is_active = False
            user.save()
        return user
