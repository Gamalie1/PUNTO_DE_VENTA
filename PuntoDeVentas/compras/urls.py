from django.urls import path
from . import views

urlpatterns = [
    path('compras/', views.CompraListView.as_view(), name='compra_list'),
    path('compras/nueva/', views.CompraCreateView.as_view(), name='compra_create'),
    path('compras/<int:pk>/editar/', views.CompraUpdateView.as_view(), name='compra_update'),
    path('compras/<int:pk>/anular/', views.anular_compra, name='anular_compra'),
    path('compras/<int:pk>/eliminar/', views.eliminar_compra, name='eliminar_compra'),
]