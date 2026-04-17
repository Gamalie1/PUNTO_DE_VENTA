from django import forms
from .models import Sucursal

class SucursalForm(forms.ModelForm):
    class Meta:
        model = Sucursal
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'moneda': forms.TextInput(attrs={'class': 'form-control'}),
            'mensaje_ticket': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
