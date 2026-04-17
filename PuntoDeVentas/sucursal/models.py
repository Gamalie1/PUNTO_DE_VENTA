from django.db import models

# Create your models here.
class Sucursal(models.Model):
    nombre = models.CharField(max_length=150)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to='empresa/', blank=True, null=True)
    mensaje_ticket = models.TextField(blank=True, help_text="Mensaje que aparecerá al final del ticket")
    fecha_inicio = models.DateField(blank=True, null=True, help_text="Fecha de inicio de operaciones")

    def __str__(self):
        return self.nombre

    def cantidad_sucursales(self):
        return self.sucursales.count()