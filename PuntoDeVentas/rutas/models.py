from django.conf import settings
from django.db import models

from inventario.models import Producto


class Ruta(models.Model):
    """Una ruta/zona de reparto (ej: 'Centro', 'Norte') a la que se le
    asignan productos y en la que se clasifican las ventas."""
    nombre = models.CharField(max_length=150, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class AsignacionDiaria(models.Model):
    """Cuanto de un producto le entrega el admin a un vendedor, en una
    ruta, para un dia especifico. Lo "vendido" y lo "restante" NO se
    guardan aqui: se calculan a partir de las ventas reales (ver
    rutas.services.calcular_progreso_asignaciones) para que nunca queden
    desincronizados con lo que en verdad se vendio.
    """
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asignaciones_diarias',
    )
    ruta = models.ForeignKey(Ruta, on_delete=models.PROTECT, related_name='asignaciones')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='asignaciones_diarias')
    fecha = models.DateField()
    cantidad_asignada = models.PositiveIntegerField()
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='asignaciones_creadas',
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', 'vendedor__username', 'producto__nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['vendedor', 'ruta', 'producto', 'fecha'],
                name='unica_asignacion_por_vendedor_ruta_producto_dia',
            )
        ]
        indexes = [
            models.Index(fields=['fecha', 'vendedor']),
        ]

    def __str__(self):
        return f"{self.producto.nombre} x{self.cantidad_asignada} - {self.vendedor} - {self.ruta} ({self.fecha})"
