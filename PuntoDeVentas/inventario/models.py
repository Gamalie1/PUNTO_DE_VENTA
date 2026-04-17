from django.db import models
import uuid
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    es_unico = models.BooleanField(default=False)  # Indicamos si es único

    def __str__(self):
        return self.nombre

    def generar_codigos_barras(self):
        """Genera códigos de barras únicos para cada unidad si el producto es único"""
        if self.es_unico:
            # Si el producto es único y tiene stock, generamos tantos códigos de barras como unidades haya en stock
            if self.stock > 0:
                for _ in range(self.stock):
                    CodigoBarras.objects.create(producto=self)
                # El stock se mantiene sin cambios
                self.save()  # Guardamos el producto con el stock original
        else:
            # Si el producto no es único, generamos solo un código de barras
            if self.stock > 0:
                # Solo generamos un código de barras para el producto no único
                CodigoBarras.objects.create(producto=self)
                self.save()  # Guardamos el producto con el stock original


class CodigoBarras(models.Model):
    producto = models.ForeignKey(Producto, related_name="codigos_barras", on_delete=models.CASCADE)
    codigo = models.CharField(max_length=255, unique=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = str(uuid.uuid4())  # Genera un código único si no existe
        super().save(*args, **kwargs)

    def __str__(self):
        return self.codigo
    
class HistorialStock(models.Model):
    producto = models.ForeignKey(Producto, related_name='historial_stock', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()  # Cantidad que se añadió o restó del stock
    tipo_cambio = models.CharField(max_length=100, choices=[('añadido', 'Añadido'), ('vendido', 'Vendido'), ('ajuste', 'Ajuste')])
    fecha = models.DateTimeField(default=timezone.now)
    comentario = models.TextField(blank=True, null=True)  # Comentarios adicionales sobre el cambio

    def __str__(self):
        return f'{self.cantidad} unidades {self.tipo_cambio} para {self.producto.nombre}'
