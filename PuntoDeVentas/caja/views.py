from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import Caja, Transaccion, CorteCaja
from ventas.models import Venta
from .forms import CorteCajaForm
from django.db.models import Sum
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.db import models
from django.template.loader import render_to_string
from weasyprint import HTML
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from usuarios.permissions import RolRequiredMixin
from .services import filtrar_cajas
from PuntoDeVentas.exports import exportar_excel, exportar_pdf

class CajaListView(LoginRequiredMixin, ListView):
    model = Caja
    template_name = 'caja_list.html'
    context_object_name = 'cajas'
    paginate_by = 15

    def get_queryset(self):
        return filtrar_cajas(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas para tarjetas (ahora también deben considerar el filtro de rol)
        user = self.request.user
        if user.rol == 'ADMIN':
            cajas = Caja.objects.all()
        else:
            cajas = Caja.objects.filter(usuario_apertura=user)  # mismo campo
        
        context['total_cajas'] = cajas.count()
        context['cajas_abiertas'] = cajas.filter(cerrado=False).count()
        context['cajas_cerradas'] = cajas.filter(cerrado=True).count()
        
        return context

class CajaCreateView(RolRequiredMixin, CreateView):
    roles_permitidos = ('ADMIN',)
    model = Caja
    template_name = 'caja_form.html'
    fields = ['nombre', 'saldo_inicial']
    success_url = reverse_lazy('caja_list')

    def form_valid(self, form):
        # Asignar el usuario autenticado como usuario_apertura
        form.instance.usuario_apertura = self.request.user
        # Establecer el saldo_actual igual al saldo_inicial
        form.instance.saldo_actual = form.instance.saldo_inicial
        return super().form_valid(form)

# Vista para registrar ingresos/egresos
class TransaccionCreateView(LoginRequiredMixin, CreateView):
    model = Transaccion
    template_name = 'transaccion_form.html'
    fields = ['caja', 'tipo', 'monto', 'descripcion']

    def form_valid(self, form):
        form.instance.save()  # Guardamos la transacción
        caja = form.instance.caja

        # Actualizamos el saldo según el tipo de transacción
        if form.instance.tipo == 'INGRESO':
            caja.agregar_ingreso(form.instance.monto)
        elif form.instance.tipo == 'EGRESO':
            caja.agregar_egreso(form.instance.monto)

        return super().form_valid(form)

    success_url = reverse_lazy('caja_list')



# Vista para los detalles de una caja y para cerrarla
class CajaDetailView(LoginRequiredMixin, UpdateView):
    model = Caja
    template_name = 'caja_detail.html'
    fields = ['nombre', 'saldo_actual', 'cerrado']  # Los campos que se van a mostrar
    context_object_name = 'caja'

    def form_valid(self, form):
        if form.instance.cerrado and not form.instance.fecha_cierre:
            form.instance.cerrar_caja()  # Cierra la caja si se marca como cerrada
        return super().form_valid(form)

    success_url = reverse_lazy('caja_list')  # Redirigir a la lista de cajas después de guardar los cambios


@login_required
def registrar_corte_caja(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id, cerrado=False)
    
    # Verificar corte duplicado hoy
    if CorteCaja.objects.filter(caja=caja, fecha_corte__date=timezone.now().date()).exists():
        messages.warning(request, 'Ya existe un corte para esta caja hoy.')
        return redirect('caja_list')

    fecha_inicio = caja.fecha_apertura
    fecha_fin = timezone.now()

    # Transacciones del período
    transacciones = Transaccion.objects.filter(
        caja=caja,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).order_by('-fecha')

    # Ventas del período (para mostrar en template)
    # select_related('cliente') evita una consulta extra por cada venta
    # al renderizar venta.cliente.nombre en la tabla del corte.
    ventas = Venta.objects.filter(
        caja=caja,
        fecha__gte=fecha_inicio,
        fecha__lte=fecha_fin
    ).select_related('cliente').order_by('-fecha')

    # Totales
    ingresos = transacciones.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    egresos = transacciones.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
    total_ventas = ventas.aggregate(Sum('total'))['total__sum'] or 0
    saldo_esperado = (caja.saldo_inicial or 0) + ingresos - egresos

    if request.method == 'POST':
        form = CorteCajaForm(request.POST)
        if form.is_valid():
            corte = form.save(commit=False)
            corte.caja = caja
            corte.fecha_inicio = fecha_inicio
            corte.fecha_fin = fecha_fin
            corte.saldo_inicial = caja.saldo_inicial
            corte.saldo_final = saldo_esperado
            corte.usuario_cierre = request.user
            corte.save()
            corte.transacciones.set(transacciones)
            corte.calcular_totales()
            
            if corte.monto_fisico:
                corte.calcular_diferencia()
            
            caja.cerrar_caja(usuario=request.user)
            messages.success(request, f'Corte #{corte.id} realizado exitosamente.')
            return redirect('caja_list')
    else:
        form = CorteCajaForm()

    return render(request, 'corte_caja_form.html', {
        'form': form,
        'caja': caja,
        'saldo_inicial': caja.saldo_inicial,
        'ingresos': ingresos,
        'egresos': egresos,
        'total_ventas': total_ventas,
        'saldo_esperado': saldo_esperado,
        'transacciones': transacciones[:10],
        'ventas': ventas[:10],
        'total_transacciones': transacciones.count(),
        'total_ventas_count': ventas.count(),
    })

class CorteCajaListView(LoginRequiredMixin, ListView):
    model = CorteCaja
    template_name = 'corte_caja_list.html'
    context_object_name = 'cortes'
    paginate_by = 10  # Opcional: Paginación

    def get_queryset(self):
        # Obtener el ID de la caja desde la URL
        caja_id = self.kwargs['caja_id']

        # Filtrar los cortes de caja por la caja seleccionada
        # select_related('caja') evita una consulta extra por cada fila
        # al renderizar corte.caja.nombre en la tabla.
        return CorteCaja.objects.filter(caja_id=caja_id).select_related('caja')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener la caja seleccionada por su ID
        caja_id = self.kwargs['caja_id']
        context['caja'] = get_object_or_404(Caja, id=caja_id)
        return context

# Vista para mostrar los detalles de un corte de caja
class CorteCajaDetailView(LoginRequiredMixin, DetailView):
    model = CorteCaja
    template_name = 'corte_caja_detail.html'
    context_object_name = 'corte'
    queryset = CorteCaja.objects.select_related('caja', 'usuario_cierre')

@login_required
def registrar_ingresos_egresos(request, caja_id):
    caja = get_object_or_404(Caja, id=caja_id)

    # 🚨 VALIDAR SI LA CAJA ESTÁ CERRADA
    if caja.cerrado:
        messages.error(request, "La caja ya está cerrada.")
        return redirect('caja_list')

    transacciones = Transaccion.objects.filter(caja=caja).order_by('-fecha')
    cortes = CorteCaja.objects.filter(caja=caja)

    if request.method == 'POST':

        # 🔹 Validar monto
        try:
            monto = Decimal(request.POST.get('monto'))
        except (TypeError, InvalidOperation):
            monto = Decimal('0')

        descripcion = request.POST.get('descripcion')
        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO')

        if monto <= 0:
            messages.error(request, "El monto debe ser mayor a 0.")
            return redirect('registrar_ingresos_egresos', caja_id=caja.id)

        # 🔥 IDENTIFICAR TIPO
        tipo = None
        if 'ingreso' in request.POST:
            tipo = 'INGRESO'
        elif 'egreso' in request.POST:
            tipo = 'EGRESO'

        if not tipo:
            messages.error(request, "Tipo de operación inválido.")
            return redirect('registrar_ingresos_egresos', caja_id=caja.id)

        # 🔥 CREAR TRANSACCIÓN
        transaccion = Transaccion.objects.create(
            caja=caja,
            tipo=tipo,
            metodo_pago=metodo_pago,
            monto=monto,
            descripcion=descripcion
        )

        # 🔥 ACTUALIZAR CAJA
        if tipo == 'INGRESO':
            caja.agregar_ingreso(monto)
            messages.success(request, f"Ingreso de ${monto} registrado.")
        else:
            caja.agregar_egreso(monto)
            messages.success(request, f"Egreso de ${monto} registrado.")

        return redirect('registrar_ingresos_egresos', caja_id=caja.id)

    return render(request, 'corte_caja_list.html', {
        'caja': caja,
        'transacciones': transacciones,
        'cortes': cortes
    })

@login_required
def generar_pdf_corte(request, corte_id):
    corte = CorteCaja.objects.get(id=corte_id)
    
    # Determinar la fecha del corte (si tiene campo fecha, úsalo; si no, fecha actual)
    # Ajusta 'fecha' por el nombre real de tu campo (ej. 'fecha_corte', 'created_at')
    if hasattr(corte, 'fecha') and corte.fecha:
        fecha_str = corte.fecha.strftime('%Y%m%d')  # Formato: AAAAMMDD
    else:
        fecha_str = timezone.now().strftime('%Y%m%d')
    
    # Nombre del archivo con fecha
    nombre_archivo = f'corte_{corte.id}_{fecha_str}.pdf'
    
    html_string = render_to_string('corte_pdf.html', {
        'corte': corte,
        'transacciones': corte.transacciones.all()
    })
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    # Generar PDF con WeasyPrint
    HTML(string=html_string).write_pdf(response)
    
    return response

@login_required
def ticket_corte(request, corte_id):
    corte = CorteCaja.objects.get(id=corte_id)
    transacciones = corte.transacciones.all()

    return render(request, "ticket_corte.html", {
        "corte": corte,
        "transacciones": transacciones
    })


def _filas_cajas(request):
    encabezados = ['Nombre', 'Saldo inicial', 'Saldo actual', 'Estado', 'Apertura', 'Cierre', 'Abierta por']
    filas = []
    for caja in filtrar_cajas(request):
        filas.append([
            caja.nombre,
            float(caja.saldo_inicial),
            float(caja.saldo_actual),
            'Cerrada' if caja.cerrado else 'Abierta',
            caja.fecha_apertura.strftime('%d/%m/%Y %H:%M'),
            caja.fecha_cierre.strftime('%d/%m/%Y %H:%M') if caja.fecha_cierre else '-',
            caja.usuario_apertura.get_username() if caja.usuario_apertura else '-',
        ])
    return encabezados, filas


@login_required
def exportar_cajas_excel(request):
    encabezados, filas = _filas_cajas(request)
    return exportar_excel('cajas', encabezados, filas, titulo_hoja='Cajas')


@login_required
def exportar_cajas_pdf(request):
    encabezados, filas = _filas_cajas(request)
    return exportar_pdf('cajas', 'Listado de Cajas', encabezados, filas)




