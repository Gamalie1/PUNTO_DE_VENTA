
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Sucursal
from usuarios.permissions import RolRequiredMixin
from django.contrib import messages
# Vista para listar las sucursales
class SucursalListView(LoginRequiredMixin, ListView):
    model = Sucursal
    template_name = 'sucursal_list.html'
    context_object_name = 'sucursales'
    paginate_by = 10  # Limitar a 10 sucursales por página

# Crear sucursal
class SucursalCreateView(RolRequiredMixin, CreateView):
    roles_permitidos = ('ADMIN',)
    model = Sucursal
    template_name = 'sucursal_form.html'
    fields = ['nombre', 'direccion', 'telefono', 'email', 'logo', 'mensaje_ticket', 'fecha_inicio']
    success_url = reverse_lazy('sucursal_list')

    def form_valid(self, form):
        messages.success(self.request, f"La sucursal {form.instance.nombre} fue registrada correctamente.")
        return super().form_valid(form)


# Editar sucursal
class SucursalUpdateView(RolRequiredMixin, UpdateView):
    roles_permitidos = ('ADMIN',)
    model = Sucursal
    template_name = 'sucursal_form.html'
    fields = ['nombre', 'direccion', 'telefono', 'email', 'logo', 'mensaje_ticket', 'fecha_inicio']
    success_url = reverse_lazy('sucursal_list')

    def form_valid(self, form):
        messages.success(self.request, f"La sucursal {form.instance.nombre} fue actualizada correctamente.")
        return super().form_valid(form)


# Eliminar sucursal
class SucursalDeleteView(RolRequiredMixin, DeleteView):
    roles_permitidos = ('ADMIN',)
    model = Sucursal
    template_name = 'sucursal_confirm_delete.html'
    success_url = reverse_lazy('sucursal_list')

    def post(self, request, *args, **kwargs):
        sucursal = self.get_object()
        messages.success(self.request, f"La sucursal {sucursal.nombre} fue eliminada correctamente.")
        return super().post(request, *args, **kwargs)