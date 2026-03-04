from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class UsuarioForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "telefono",
            "password1",
            "password2",
        ]