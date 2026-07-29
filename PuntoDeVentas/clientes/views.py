from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import ClienteForm
from django.contrib import messages
from PuntoDeVentas.exports import exportar_excel, exportar_pdf

class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'lista.html'
    context_object_name = 'clientes'
    ordering = ['-fecha_registro']

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'formulario.html'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        messages.success(self.request, "Cliente registrado con éxito.")
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'formulario.html'
    success_url = reverse_lazy('clientes:lista')

    def form_valid(self, form):
        messages.success(self.request, "El cliente fue actualizado correctamente.")
        return super().form_valid(form)


class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'eliminar.html'
    success_url = reverse_lazy('clientes:lista')

    def post(self, request, *args, **kwargs):
        messages.success(self.request, "El cliente fue eliminado correctamente.")
        return super().post(request, *args, **kwargs)


def _filas_clientes():
    encabezados = ['Nombre', 'Teléfono', 'Email', 'Dirección', 'Fecha de registro']
    filas = []
    for cliente in Cliente.objects.all().order_by('-fecha_registro'):
        filas.append([
            cliente.nombre,
            cliente.telefono or '-',
            cliente.email or '-',
            cliente.direccion or '-',
            cliente.fecha_registro.strftime('%d/%m/%Y %H:%M'),
        ])
    return encabezados, filas


@login_required
def exportar_clientes_excel(request):
    encabezados, filas = _filas_clientes()
    return exportar_excel('clientes', encabezados, filas, titulo_hoja='Clientes')


@login_required
def exportar_clientes_pdf(request):
    encabezados, filas = _filas_clientes()
    return exportar_pdf('clientes', 'Listado de Clientes', encabezados, filas)
