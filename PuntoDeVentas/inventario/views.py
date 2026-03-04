from django.shortcuts import render
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from .models import Producto
# Create your views here.
class ProductoListView(ListView):
    model = Producto
    template_name = "lista_productos.html"
    context_object_name = "productos"


class ProductoCreateView(CreateView):
    model = Producto
    fields = ['nombre', 'descripcion', 'precio', 'stock', 'imagen']
    template_name = "crear_producto.html"
    success_url = reverse_lazy("lista_productos")