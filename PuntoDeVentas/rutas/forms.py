from django import forms

from usuarios.models import Usuario

from .models import AsignacionDiaria, Ruta


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ['nombre', 'descripcion', 'activa']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AsignacionDiariaForm(forms.ModelForm):
    class Meta:
        model = AsignacionDiaria
        fields = ['vendedor', 'ruta', 'producto', 'fecha', 'cantidad_asignada']
        widgets = {
            'vendedor': forms.Select(attrs={'class': 'form-control'}),
            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad_asignada': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vendedor'].queryset = Usuario.objects.filter(rol__in=['CAJERO', 'ALMACEN'])
        self.fields['ruta'].queryset = Ruta.objects.filter(activa=True)
