# gmtisp_enduser/forms.py

from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=128, required=True, widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
