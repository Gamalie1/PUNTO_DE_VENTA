from django.shortcuts import render,  redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Usuario
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView,  LogoutView
from .forms import UsuarioForm, UsuarioEditForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from ventas.models import Venta, DetalleVenta
from datetime import datetime, timedelta
from inventario.models import Producto
from clientes.models import Cliente
from compras.models import CompraGeneral
from django.contrib.auth.forms import PasswordChangeForm

def index(request):
    # ========== DATOS GENERALES ==========
    fecha_actual = timezone.now()
    fecha_inicio_dia = fecha_actual.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fecha_inicio_mes = fecha_actual.replace(day=1, hour=0, minute=0, second=0)
    fecha_inicio_anio = fecha_actual.replace(month=1, day=1, hour=0, minute=0, second=0)
    
    # Ventas totales (sin filtro de estado)
    total_ventas = Venta.objects.count()
    total_recaudado = Venta.objects.aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas del día
    ventas_hoy = Venta.objects.filter(
        fecha__gte=fecha_inicio_dia
    ).count()
    recaudado_hoy = Venta.objects.filter(
        fecha__gte=fecha_inicio_dia
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas de la semana
    ventas_semana = Venta.objects.filter(
        fecha__gte=fecha_inicio_semana
    ).count()
    recaudado_semana = Venta.objects.filter(
        fecha__gte=fecha_inicio_semana
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas del mes
    ventas_mes = Venta.objects.filter(
        fecha__gte=fecha_inicio_mes
    ).count()
    recaudado_mes = Venta.objects.filter(
        fecha__gte=fecha_inicio_mes
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ventas del año
    ventas_anio = Venta.objects.filter(
        fecha__gte=fecha_inicio_anio
    ).count()
    recaudado_anio = Venta.objects.filter(
        fecha__gte=fecha_inicio_anio
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Productos con bajo stock (menos de 10 unidades)
    productos_bajo_stock = Producto.objects.filter(stock__lt=10).count()
    productos_agotados = Producto.objects.filter(stock=0).count()
    
    # Clientes registrados
    total_clientes = Cliente.objects.count()
    
    # Compras del mes
    compras_mes = CompraGeneral.objects.filter(
        fecha__gte=fecha_inicio_mes
    ).count()
    inversion_mes = CompraGeneral.objects.filter(
        fecha__gte=fecha_inicio_mes
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Ganancia estimada (ventas - compras)
    ganancia_estimada = total_recaudado - inversion_mes
    
    # Ticket promedio
    ticket_promedio = total_recaudado / total_ventas if total_ventas > 0 else 0
    
    # ========== DATOS PARA GRÁFICOS ==========
    
    # Gráfico por día (últimos 7 días)
    dias = []
    ventas_dias = []
    for i in range(6, -1, -1):
        fecha = fecha_actual - timedelta(days=i)
        fecha_inicio = fecha.replace(hour=0, minute=0, second=0)
        fecha_fin = fecha.replace(hour=23, minute=59, second=59)
        
        total_dia = Venta.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        dias.append(fecha.strftime('%d/%m'))
        ventas_dias.append(float(total_dia))
    
    # Gráfico por semana (últimas 4 semanas)
    semanas = []
    ventas_semanas = []
    for i in range(3, -1, -1):
        fecha_inicio_semana = fecha_actual - timedelta(weeks=i)
        fecha_inicio_semana = fecha_inicio_semana - timedelta(days=fecha_inicio_semana.weekday())
        fecha_fin_semana = fecha_inicio_semana + timedelta(days=6)
        
        total_semana = Venta.objects.filter(
            fecha__gte=fecha_inicio_semana,
            fecha__lte=fecha_fin_semana
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        semanas.append(f"Sem {fecha_inicio_semana.strftime('%d/%m')}")
        ventas_semanas.append(float(total_semana))
    
    # Gráfico por mes (últimos 6 meses)
    meses = []
    ventas_meses = []
    for i in range(5, -1, -1):
        fecha_mes = fecha_actual - timedelta(days=30*i)
        fecha_inicio_mes = fecha_mes.replace(day=1, hour=0, minute=0, second=0)
        
        if i == 0:
            fecha_fin_mes = fecha_actual
        else:
            if fecha_mes.month == 12:
                fecha_fin_mes = fecha_mes.replace(year=fecha_mes.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fecha_fin_mes = fecha_mes.replace(month=fecha_mes.month+1, day=1) - timedelta(days=1)
        
        total_mes = Venta.objects.filter(
            fecha__gte=fecha_inicio_mes,
            fecha__lte=fecha_fin_mes
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        meses.append(fecha_mes.strftime('%B %Y'))
        ventas_meses.append(float(total_mes))
    
    # Gráfico por año (últimos 5 años)
    años = []
    ventas_años = []
    año_actual = fecha_actual.year
    for i in range(4, -1, -1):
        año = año_actual - i
        fecha_inicio_año = datetime(año, 1, 1)
        fecha_fin_año = datetime(año, 12, 31, 23, 59, 59)
        
        total_año = Venta.objects.filter(
            fecha__gte=fecha_inicio_año,
            fecha__lte=fecha_fin_año
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        años.append(str(año))
        ventas_años.append(float(total_año))
    
    # Top 5 productos más vendidos
    productos_top = DetalleVenta.objects.values('producto__nombre').annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:5]
    
    # Últimas 5 ventas
    ultimas_ventas = Venta.objects.order_by('-fecha')[:5]
    
    context = {
        # Tarjetas
        'total_ventas': total_ventas,
        'total_recaudado': total_recaudado,
        'recaudado_hoy': recaudado_hoy,
        'ventas_hoy': ventas_hoy,
        'recaudado_semana': recaudado_semana,
        'ventas_semana': ventas_semana,
        'recaudado_mes': recaudado_mes,
        'ventas_mes': ventas_mes,
        'recaudado_anio': recaudado_anio,
        'ventas_anio': ventas_anio,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_agotados': productos_agotados,
        'total_clientes': total_clientes,
        'compras_mes': compras_mes,
        'inversion_mes': inversion_mes,
        'ganancia_estimada': ganancia_estimada,
        'ticket_promedio': ticket_promedio,
        
        # Gráficos
        'dias': dias,
        'ventas_dias': ventas_dias,
        'semanas': semanas,
        'ventas_semanas': ventas_semanas,
        'meses': meses,
        'ventas_meses': ventas_meses,
        'años': años,
        'ventas_años': ventas_años,
        
        # Tablas
        'productos_top': productos_top,
        'ultimas_ventas': ultimas_ventas,
    }
    
    return render(request, 'index.html', context)

class UsuarioListView( ListView):
    model = Usuario
    template_name = "lista_usuarios.html"


@login_required
def crear_usuario(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])
            user.save()
            # Guardar la relación muchos a muchos (módulos permitidos)
            form.save_m2m()  # Esto guarda modulos_permitidos automáticamente
            messages.success(request, "Usuario creado correctamente")
            return redirect(reverse_lazy("usuarios:usuarios_lista"))
        else:
            messages.error(request, "Hubo un error al crear el usuario.")
    else:
        form = UsuarioForm()
    return render(request, "form.html", {"form": form})

class UsuarioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEditForm
    template_name = "usuario_editar.html"
    success_url = reverse_lazy("usuarios:usuarios_lista")

    def test_func(self):
        """Solo administradores pueden editar usuarios (o el propio usuario si se permite)."""
        user = self.get_object()
        # Permitir si el usuario actual es admin o si está editando su propio perfil
        return self.request.user.rol == 'ADMIN' or self.request.user == user

    def get_object(self):
        return get_object_or_404(Usuario, pk=self.kwargs['pk'])

    def form_valid(self, form):
        user = form.save(commit=False)
        
        # Manejo de contraseña (solo si se proporciona)
        password1 = self.request.POST.get("password1")
        password2 = self.request.POST.get("password2")
        
        if password1 or password2:
            if password1 and password2 and password1 == password2:
                user.set_password(password1)
                # Opcional: mantener la sesión activa después de cambiar contraseña
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(self.request, user)
                messages.success(self.request, "Contraseña actualizada correctamente.")
            else:
                form.add_error(None, "Las contraseñas no coinciden o están incompletas.")
                return self.form_invalid(form)
        
        user.save()
        
        # Guardar los módulos permitidos (campo many-to-many)
        # El formulario ya tiene el campo 'modulos_permitidos', lo asignamos
        if 'modulos_permitidos' in form.cleaned_data:
            user.modulos_permitidos.set(form.cleaned_data['modulos_permitidos'])
        
        messages.success(self.request, f"El usuario {user.username} fue actualizado correctamente.")
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Hubo errores en el formulario. Por favor corrige los campos.")
        return super().form_invalid(form)


class UsuarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Usuario
    template_name = "eliminar.html"
    success_url = reverse_lazy("usuarios:usuarios_lista")

    def form_valid(self, form):
        usuario = self.get_object()
        messages.success(self.request, f"El usuario {usuario.username} fue eliminado correctamente.")
        return super().form_valid(form)



class LoginUsuarioView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("usuarios:informacion")


class LogoutUsuarioView(LogoutView):
    next_page = reverse_lazy("login")
