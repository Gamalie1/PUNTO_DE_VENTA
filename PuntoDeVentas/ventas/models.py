from django.db import models
from inventario.models import Producto
from clientes.models import Cliente
from django.conf import settings


# Create your models here.
class Venta(models.Model):
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    numero_ticket = models.CharField(max_length=20, unique=True, blank=True, null=True)
    # Campos adicionales para el pago
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cambio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    caja = models.ForeignKey('caja.Caja', on_delete=models.SET_NULL, null=True, blank=True)
    
  
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.numero_ticket:
            self.numero_ticket = f"VT-{self.id:05d}"
            super().save(update_fields=["numero_ticket"])
    
    def __str__(self):
        return f"Venta #{self.numero_ticket} - {self.fecha}"  # Usar el numero_ticket para que aparezca en la visualización

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio
    

