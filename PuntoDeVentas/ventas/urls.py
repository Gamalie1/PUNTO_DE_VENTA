from django.urls import path
from .views import (
    VentaListView, VentaDetailView, guardar_pago, punto_venta, imprimir_ticket,
    descargar_ticket, api_buscar_por_codigo, exportar_ventas_excel, exportar_ventas_pdf,
)

urlpatterns = [
    path('', punto_venta, name='punto_venta'),
    path('ventas/', VentaListView.as_view(), name='venta_list'),  # Ruta para listar ventas
    path('venta/<int:pk>/', VentaDetailView.as_view(), name='venta_detail'),  # Detalles de venta
   path('guardar_pago/', guardar_pago, name='guardar_pago'),  # Ruta para guardar el pago
   path('ticket/<int:venta_id>/',imprimir_ticket, name='imprimir_ticket'),
  path('ticket/descargar/<int:venta_id>/', descargar_ticket, name='descargar_ticket'),
  path('ventas/api/buscar-codigo/', api_buscar_por_codigo, name='api_buscar_codigo'),
  path('ventas/exportar/excel/', exportar_ventas_excel, name='exportar_ventas_excel'),
  path('ventas/exportar/pdf/', exportar_ventas_pdf, name='exportar_ventas_pdf'),
]