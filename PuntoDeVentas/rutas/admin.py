from django.contrib import admin

from .models import AsignacionDiaria, Ruta


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)


@admin.register(AsignacionDiaria)
class AsignacionDiariaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'vendedor', 'ruta', 'producto', 'cantidad_asignada')
    list_filter = ('fecha', 'ruta', 'vendedor')
    search_fields = ('producto__nombre', 'vendedor__username')
    date_hierarchy = 'fecha'
