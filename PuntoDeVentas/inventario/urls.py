from django.urls import path
from . import views as Productos_views

urlpatterns = [
    path('inventario/', Productos_views.lista_productos, name='lista_productos'),
    path('nuevo/', Productos_views.registrar_producto, name='crear_producto'),
     path('producto/editar/<int:pk>/', Productos_views.editar_producto, name='editar_producto'),
    path('producto/eliminar/<int:pk>/', Productos_views.eliminar_producto, name='eliminar_producto'),
    path('inventario/<int:pk>/etiqueta-pdf/', Productos_views.producto_etiqueta_pdf, name='producto_etiqueta_pdf'),
    path('producto/<int:pk>/agregar-stock/', Productos_views.agregar_stock, name='agregar_stock'),
    path('inventario/exportar/excel/', Productos_views.exportar_productos_excel, name='exportar_productos_excel'),
    path('inventario/exportar/pdf/', Productos_views.exportar_productos_pdf, name='exportar_productos_pdf'),
]