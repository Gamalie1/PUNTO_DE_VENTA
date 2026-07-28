from django.db.models import Sum

from ventas.models import DetalleVenta


def calcular_progreso_asignaciones(asignaciones):
    """Anota cada AsignacionDiaria con .vendido y .restante.

    Estos valores no se guardan en la base: se calculan aqui a partir de
    las ventas reales (DetalleVenta) para que nunca queden desincronizados
    del stock/ventas reales, el mismo error que tenia el campo `stock` de
    productos unicos antes de corregirlo.

    Usa una sola consulta agregada para todas las asignaciones recibidas
    (en vez de una consulta por asignacion) para evitar N+1.
    """
    asignaciones = list(asignaciones)
    if not asignaciones:
        return asignaciones

    fechas = {a.fecha for a in asignaciones}
    vendedores_ids = {a.vendedor_id for a in asignaciones}

    ventas_agrupadas = (
        DetalleVenta.objects.filter(
            venta__fecha__date__in=fechas,
            venta__vendedor_id__in=vendedores_ids,
        )
        .values('producto_id', 'venta__vendedor_id', 'venta__ruta_id', 'venta__fecha__date')
        .annotate(total=Sum('cantidad'))
    )

    vendido_por_combo = {
        (
            fila['producto_id'],
            fila['venta__vendedor_id'],
            fila['venta__ruta_id'],
            fila['venta__fecha__date'],
        ): fila['total']
        for fila in ventas_agrupadas
    }

    for asignacion in asignaciones:
        clave = (asignacion.producto_id, asignacion.vendedor_id, asignacion.ruta_id, asignacion.fecha)
        vendido = vendido_por_combo.get(clave, 0)
        asignacion.vendido = vendido
        asignacion.restante = max(asignacion.cantidad_asignada - vendido, 0)

    return asignaciones
