from django.db import models
from django.conf import settings

class CompraGeneral(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.CharField(max_length=255)
    cantidad = models.PositiveIntegerField(default=0, help_text="Cantidad general (opcional)")
    total = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monto total pagado")
    observaciones = models.TextField(blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    estado = models.BooleanField(default=True, help_text="Activo = True, Anulado = False")

    def __str__(self):
        return f"{self.fecha.strftime('%d/%m/%Y')} - {self.descripcion} - ${self.total}"