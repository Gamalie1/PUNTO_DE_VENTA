from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Cliente
from .forms import ClienteForm
from django.contrib import messages

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
    

