from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.ClienteListView.as_view(), name='lista'),
    path('nuevo/', views.ClienteCreateView.as_view(), name='crear'),
    path('editar/<int:pk>/', views.ClienteUpdateView.as_view(), name='editar'),
    path('eliminar/<int:pk>/', views.ClienteDeleteView.as_view(), name='eliminar'),
]
