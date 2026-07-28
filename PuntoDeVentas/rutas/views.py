from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, UpdateView

from usuarios.permissions import RolRequiredMixin

from .forms import AsignacionDiariaForm, RutaForm
from .models import AsignacionDiaria, Ruta
from .services import calcular_progreso_asignaciones


class RutaListView(RolRequiredMixin, ListView):
    roles_permitidos = ('ADMIN',)
    model = Ruta
    template_name = 'ruta_list.html'
    context_object_name = 'rutas'


class RutaCreateView(RolRequiredMixin, CreateView):
    roles_permitidos = ('ADMIN',)
    model = Ruta
    form_class = RutaForm
    template_name = 'ruta_form.html'
    success_url = reverse_lazy('rutas:ruta_list')

    def form_valid(self, form):
        messages.success(self.request, f"Ruta '{form.instance.nombre}' creada correctamente.")
        return super().form_valid(form)


class RutaUpdateView(RolRequiredMixin, UpdateView):
    roles_permitidos = ('ADMIN',)
    model = Ruta
    form_class = RutaForm
    template_name = 'ruta_form.html'
    success_url = reverse_lazy('rutas:ruta_list')

    def form_valid(self, form):
        messages.success(self.request, f"Ruta '{form.instance.nombre}' actualizada correctamente.")
        return super().form_valid(form)


class AsignacionDiariaListView(RolRequiredMixin, ListView):
    """Panel del admin: cuanto se le entrego hoy a cada vendedor/ruta y
    cuanto lleva vendido, para ver de un vistazo el restante del dia."""
    roles_permitidos = ('ADMIN',)
    model = AsignacionDiaria
    template_name = 'asignacion_list.html'
    context_object_name = 'asignaciones'

    def get_fecha(self):
        fecha_str = self.request.GET.get('fecha')
        if fecha_str:
            try:
                return timezone.datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        return timezone.localdate()

    def get_queryset(self):
        fecha = self.get_fecha()
        return (
            AsignacionDiaria.objects.filter(fecha=fecha)
            .select_related('vendedor', 'ruta', 'producto')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['asignaciones'] = calcular_progreso_asignaciones(context['asignaciones'])
        context['fecha'] = self.get_fecha()
        return context


class AsignacionDiariaCreateView(RolRequiredMixin, CreateView):
    roles_permitidos = ('ADMIN',)
    model = AsignacionDiaria
    form_class = AsignacionDiariaForm
    template_name = 'asignacion_form.html'
    success_url = reverse_lazy('rutas:asignacion_list')

    def get_initial(self):
        return {'fecha': timezone.localdate()}

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(
            self.request,
            f"Se asignaron {form.instance.cantidad_asignada} unidades de "
            f"{form.instance.producto.nombre} a {form.instance.vendedor} "
            f"en la ruta {form.instance.ruta}.",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        if 'vendedor' in form.errors or '__all__' in form.errors:
            for error in form.non_field_errors():
                messages.error(self.request, error)
        return super().form_invalid(form)
