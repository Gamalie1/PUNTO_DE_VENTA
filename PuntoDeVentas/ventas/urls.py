from django.urls import path
from .views import punto_venta

urlpatterns = [
    path('', punto_venta, name='punto_venta'),
]