from django.urls import path
from .views import ProductoListView, ProductoCreateView

urlpatterns = [
    path('', ProductoListView.as_view(), name='lista_productos'),
    path('nuevo/', ProductoCreateView.as_view(), name='crear_producto'),
]