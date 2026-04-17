from django import forms
from .models import CorteCaja

class CorteCajaForm(forms.ModelForm):
    class Meta:
        model = CorteCaja
        fields = [ 'comentario']
    
