
from django.urls import path
from .views import SucursalListView, SucursalCreateView, SucursalUpdateView, SucursalDeleteView

urlpatterns = [
    path('', SucursalListView.as_view(), name='sucursal_list'),
    path('crear/', SucursalCreateView.as_view(), name='sucursal_create'),
    path('editar/<int:pk>/', SucursalUpdateView.as_view(), name='sucursal_edit'),
    path('eliminar/<int:pk>/', SucursalDeleteView.as_view(), name='sucursal_delete'),
]