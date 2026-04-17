# forms.py
from django import forms
from .models import CompraGeneral

class CompraGeneralForm(forms.ModelForm):
    class Meta:
        model = CompraGeneral
        fields = ['descripcion', 'cantidad', 'total', 'observaciones']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ej: Compra de 100 garrafones de agua'}),
            'cantidad': forms.NumberInput(attrs={'min': 0, 'step': 1, 'placeholder': 'Ej: 100'}),
            'total': forms.NumberInput(attrs={'min': 0, 'step': 0.01, 'placeholder': 'Ej: 1500.00'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Notas adicionales sobre la compra...'}),
        }
        help_texts = {
            'cantidad': 'Opcional: Ingrese la cantidad de productos comprados',
            'total': 'Monto total pagado por la compra',
        }
    
    def clean_total(self):
        total = self.cleaned_data.get('total')
        if total <= 0:
            raise forms.ValidationError('El total debe ser mayor a 0')
        return total
    
    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad and cantidad < 0:
            raise forms.ValidationError('La cantidad no puede ser negativa')
        return cantidad or 0