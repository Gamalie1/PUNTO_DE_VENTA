from datetime import datetime

from django.utils.dateparse import parse_date

from .models import Venta


def filtrar_ventas(request):
    """Aplica a Venta los mismos filtros que usa VentaListView (rol,
    busqueda por ticket, rango de fecha). La usan tanto el listado en
    pantalla como los export a Excel/PDF, para que lo que se descarga
    sea siempre exactamente lo que se esta viendo.
    """
    queryset = Venta.objects.select_related('vendedor', 'cliente', 'ruta').order_by('-fecha')

    user = request.user
    if user.rol != 'ADMIN':
        queryset = queryset.filter(vendedor=user)

    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(numero_ticket__icontains=search)

    fecha_range = request.GET.get('fecha')
    if fecha_range:
        partes = fecha_range.split(' - ')
        if len(partes) == 2:
            fecha_desde = parse_date(partes[0])
            fecha_hasta = parse_date(partes[1])
            if fecha_desde and fecha_hasta:
                fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())
                queryset = queryset.filter(fecha__range=(fecha_desde, fecha_hasta))

    return queryset
