from django.urls import path
from .views import VentaListView, VentaDetailView, guardar_pago, punto_venta, imprimir_ticket, descargar_ticket

urlpatterns = [
    path('', punto_venta, name='punto_venta'),
    path('ventas/', VentaListView.as_view(), name='venta_list'),  # Ruta para listar ventas
    path('venta/<int:pk>/', VentaDetailView.as_view(), name='venta_detail'),  # Detalles de venta
   path('guardar_pago/', guardar_pago, name='guardar_pago'),  # Ruta para guardar el pago
   path('ticket/<int:venta_id>/',imprimir_ticket, name='imprimir_ticket'),
  path('ticket/descargar/<int:venta_id>/', descargar_ticket, name='descargar_ticket'),
]