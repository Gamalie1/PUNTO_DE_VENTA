from django.urls import path

from . import views

app_name = 'rutas'

urlpatterns = [
    path('', views.RutaListView.as_view(), name='ruta_list'),
    path('nueva/', views.RutaCreateView.as_view(), name='ruta_create'),
    path('<int:pk>/editar/', views.RutaUpdateView.as_view(), name='ruta_edit'),
    path('asignaciones/', views.AsignacionDiariaListView.as_view(), name='asignacion_list'),
    path('asignaciones/nueva/', views.AsignacionDiariaCreateView.as_view(), name='asignacion_create'),
]
