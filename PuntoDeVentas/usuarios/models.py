from django.db import models
from django.contrib.auth.models import AbstractUser

class Modulo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=50, unique=True)  # ej: 'ver_usuarios', 'ver_ventas'
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

        
class Usuario(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('CAJERO', 'Cajero'),
        ('ALMACEN', 'Almacén'),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    modulos_permitidos = models.ManyToManyField(Modulo, blank=True)
    
    def __str__(self):
        return f"{self.username} - {self.rol}"
    
