from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario, Modulo

class UsuarioForm(UserCreationForm):
    modulos_permitidos = forms.ModelMultipleChoiceField(
        queryset=Modulo.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Módulos a los que tiene acceso"
    )

    class Meta:
        model = Usuario
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "telefono",
            "modulos_permitidos",
            "password1",
            "password2",
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de teléfono'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar Contraseña'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['first_name'].label = 'Nombre'
        self.fields['last_name'].label = 'Apellido'
        self.fields['email'].label = 'Correo electronico'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        
        for field_name, field in self.fields.items():
            # No aplicar 'form-control' al campo de checkboxes múltiples
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})
            field.help_text = None

class UsuarioEditForm(UserChangeForm):
    password = None  # Ocultar campo de contraseña (se maneja aparte en la vista)
    modulos_permitidos = forms.ModelMultipleChoiceField(
        queryset=Modulo.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Módulos a los que tiene acceso"
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'telefono', 'modulos_permitidos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['first_name'].label = 'Nombre'
        self.fields['last_name'].label = 'Apellido'
        self.fields['email'].label = 'Correo electrónico'
        self.fields['rol'].label = 'Rol'
        self.fields['telefono'].label = 'Teléfono'

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-control'})
            field.help_text = None