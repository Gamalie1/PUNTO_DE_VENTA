from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('CAJERO', 'Cajero'),
        ('ALMACEN', 'Almacén'),
    )
    
    rol = models.CharField(max_length=20, choices=ROLES)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.username} - {self.rol}"