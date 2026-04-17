from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'imagen', 'es_unico']  # Añadimos es_unico
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción...'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
           'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            # Aquí configuramos el campo es_unico:
           'es_unico': forms.Select(choices=[(True, 'Sí'), (False, 'No')], attrs={'class': 'form-control'}),
        }