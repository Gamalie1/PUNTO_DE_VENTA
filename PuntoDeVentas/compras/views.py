
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import CompraGeneral
from .forms import CompraGeneralForm

class CompraListView(LoginRequiredMixin, ListView):
    model = CompraGeneral
    template_name = 'compra_list.html'
    context_object_name = 'compras'
    ordering = ['-fecha']

class CompraCreateView(LoginRequiredMixin, CreateView):
    model = CompraGeneral
    form_class = CompraGeneralForm
    template_name = 'compra_form.html'
    success_url = reverse_lazy('compra_list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class CompraUpdateView(LoginRequiredMixin, UpdateView):
    model = CompraGeneral
    form_class = CompraGeneralForm
    template_name = 'compra_form.html'
    success_url = reverse_lazy('compra_list')

    def get_queryset(self):
        # Solo permitir editar compras activas (no anuladas)
        return CompraGeneral.objects.filter(estado=True)

    def form_valid(self, form):
        messages.success(self.request, 'Compra actualizada correctamente.')
        return super().form_valid(form)

@login_required
def anular_compra(request, pk):
    compra = get_object_or_404(CompraGeneral, pk=pk)
    if compra.estado:
        compra.estado = False
        compra.save()
        messages.success(request, 'Compra anulada.')
    else:
        messages.warning(request, 'Esta compra ya estaba anulada.')
    return redirect('compra_list')

# Opcional: eliminar físicamente (solo para superuser o si prefieres)
@login_required
def eliminar_compra(request, pk):
    compra = get_object_or_404(CompraGeneral, pk=pk)
    if request.user.is_superuser:
        compra.delete()
        messages.success(request, 'Compra eliminada permanentemente.')
    else:
        messages.error(request, 'No tienes permiso para eliminar.')
    return redirect('compra_list')