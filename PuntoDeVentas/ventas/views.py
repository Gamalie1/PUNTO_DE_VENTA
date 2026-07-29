from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from inventario.models import Producto, CodigoBarras
from .models import Venta, DetalleVenta
from sucursal.models import Sucursal
from django.db import transaction
from caja.services import obtener_o_abrir_caja_del_dia
import json
from django.views.generic import ListView
from django.views.generic import DetailView
from decimal import Decimal
from django.http import JsonResponse
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import HRFlowable
from datetime import datetime
from django.utils.dateparse import parse_date
from clientes.models import Cliente
from reportlab.lib.styles import ParagraphStyle
from caja.models import Transaccion
from django.contrib.auth.mixins import LoginRequiredMixin
import logging
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from rutas.models import Ruta, AsignacionDiaria
from rutas.services import calcular_progreso_asignaciones
from .services import filtrar_ventas
from PuntoDeVentas.exports import exportar_excel, exportar_pdf
# Create your views here.

@login_required
def punto_venta(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()
    # La caja del vendedor se abre sola con su primera venta del dia:
    # no se le pide llenar ningun formulario antes de poder vender.
    caja_abierta = obtener_o_abrir_caja_del_dia(request.user)

    hoy = timezone.localdate()
    # Rutas asignadas hoy a este vendedor (si no tiene ninguna, simplemente
    # no se le muestra el selector y sus ventas quedan sin ruta, como antes).
    rutas_hoy = Ruta.objects.filter(
        asignaciones__vendedor=request.user, asignaciones__fecha=hoy
    ).distinct()
    mis_asignaciones = calcular_progreso_asignaciones(
        AsignacionDiaria.objects.filter(vendedor=request.user, fecha=hoy)
        .select_related('ruta', 'producto')
    )

    contexto_base = {
        "productos": productos,
        "clientes": clientes,
        "rutas_hoy": rutas_hoy,
        "mis_asignaciones": mis_asignaciones,
    }

    if request.method == "POST":
        carrito_json = request.POST.get("carrito")
        monto_pagado = request.POST.get("monto_pagado")
        cambio = request.POST.get("cambio")
        cliente_id = request.POST.get("cliente_id")
        ruta_id = request.POST.get("ruta_id")

        if not carrito_json:
            return render(request, "punto_venta.html", {
                **contexto_base,
                "mensaje_error": "Carrito vacío"
            })

        carrito = json.loads(carrito_json)  # carrito: {producto_id: {cantidad, nombre, precio, codigos: []}}

        try:
            with transaction.atomic():
                venta = Venta.objects.create(
                    vendedor=request.user,
                    total=0,
                    caja=caja_abierta
                )

                if ruta_id:
                    try:
                        venta.ruta = Ruta.objects.get(id=ruta_id)
                    except Ruta.DoesNotExist:
                        pass

                if cliente_id and cliente_id != '':
                    try:
                        venta.cliente = Cliente.objects.get(id=cliente_id)
                    except Cliente.DoesNotExist:
                        pass

                total_venta = Decimal('0.00')

                for producto_id_str, data in carrito.items():
                    producto_id = int(producto_id_str)
                    producto = Producto.objects.select_for_update().get(id=producto_id)
                    cantidad = data['cantidad']
                    codigos_ids = data.get('codigos', [])

                    # Validar productos únicos
                    if producto.es_unico:
                        if len(codigos_ids) != cantidad:
                            raise ValueError(f"La cantidad no coincide con los códigos únicos para {producto.nombre}")
                        # Obtener los códigos de barras y verificar que no hayan sido usados
                        codigos = CodigoBarras.objects.select_for_update().filter(id__in=codigos_ids, producto=producto, usado=False)
                        if codigos.count() != cantidad:
                            raise ValueError(f"Algún código de barras de {producto.nombre} ya fue usado o es inválido")
                        # Marcar como usados
                        codigos.update(usado=True)
                        # Mantener sincronizado el contador de stock con los
                        # codigos de barras realmente disponibles (antes quedaba
                        # desactualizado para productos unicos y rompia las
                        # alertas de stock bajo/agotado del dashboard).
                        producto.stock = max(producto.stock - cantidad, 0)
                        producto.save(update_fields=['stock'])
                    else:
                        # Producto no único: validar stock
                        if producto.stock < cantidad:
                            raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")
                        # Reducir stock
                        producto.stock -= cantidad
                        producto.save()

                    # Crear detalle de venta
                    subtotal = producto.precio * cantidad
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio=producto.precio
                    )
                    total_venta += subtotal

                if total_venta == 0:
                    venta.delete()
                    return render(request, "punto_venta.html", {
                        **contexto_base,
                        "mensaje_error": "No se pudo procesar la venta (total cero)"
                    })

                venta.total = total_venta
                venta.monto_pagado = Decimal(monto_pagado) if monto_pagado else None
                venta.cambio = Decimal(cambio) if cambio else None
                venta.save()

                # Registrar transacción de ingreso
                Transaccion.objects.create(
                    caja=caja_abierta,
                    tipo='INGRESO',
                    metodo_pago='EFECTIVO',
                    monto=total_venta,
                    descripcion=f"Venta #{venta.numero_ticket or venta.id}",
                    venta=venta
                )

                return render(request, "punto_venta.html", {
                    **contexto_base,
                    "success": True,
                    "venta_id": venta.id
                })

        except Exception as e:
            # Si ocurre un error, mostrar mensaje adecuado
            return render(request, "punto_venta.html", {
                **contexto_base,
                "mensaje_error": str(e)
            })

    return render(request, "punto_venta.html", contexto_base)

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'venta_list.html'
    context_object_name = 'ventas'
    paginate_by = 20

    def get_queryset(self):
        return filtrar_ventas(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['fecha'] = self.request.GET.get('fecha', '')
        return context
    
class VentaDetailView(LoginRequiredMixin, DetailView):
    model = Venta
    template_name = 'venta_detail.html'
    context_object_name = 'venta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # self.object ya esta cargado por DetailView.get(); volver a llamar
        # a self.get_object() aqui repetiria la consulta a la base de datos.
        # select_related('producto') evita una consulta extra por cada
        # linea de la venta al renderizar detalle.producto.nombre.
        context['detalles'] = self.object.detalles.select_related('producto').all()
        return context
    
@login_required
def guardar_pago(request):
    if request.method == 'POST':
        # Obtener el venta_id del formulario
        venta_id = request.POST.get('venta_id')
        try:
            monto_pagado = Decimal(request.POST.get('monto_pagado', '0'))
            cambio = Decimal(request.POST.get('cambio', '0'))
        except:
            return JsonResponse({'success': False, 'message': 'Los valores de monto pagado y cambio no son válidos.'})

        # Verifica si la venta_id es válida
        if not venta_id or not venta_id.isdigit():
            return JsonResponse({'success': False, 'message': 'Venta no encontrada. ID inválido.'})

        # Obtener la venta correspondiente
        try:
            venta = Venta.objects.get(id=venta_id)
        except Venta.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Venta no encontrada.'})

        # Verificar si el monto pagado es mayor o igual al total de la venta
        if monto_pagado < venta.total:
            return JsonResponse({'success': False, 'message': 'El monto pagado es menor que el total de la venta.'})

        # Verificar que el cambio calculado sea correcto
        if monto_pagado < venta.total:
            return JsonResponse({'success': False, 'message': 'El monto pagado es menor que el total de la venta.'})
        
        if cambio != (monto_pagado - venta.total):
            return JsonResponse({'success': False, 'message': 'El cambio calculado no es correcto.'})

        # Actualiza la venta con el monto pagado y el cambio
        venta.monto_pagado = monto_pagado
        venta.cambio = cambio
        venta.save()

        # Aquí puedes realizar cualquier otra lógica, como cerrar la venta si es necesario
        venta.estado = 'cerrada'  # Si necesitas marcar la venta como cerrada
        venta.save()

        return JsonResponse({'success': True, 'message': 'Pago guardado correctamente.'})

    return JsonResponse({'success': False, 'message': 'Error al procesar el pago.'})

@login_required
def descargar_ticket(request, venta_id):
    """Genera el ticket en PDF con el tamano real de un rollo termico de
    58mm (no una hoja carta con una tabla angosta simulando un ticket).

    El alto de la "pagina" se calcula segun cuantas lineas va a ocupar
    el contenido (cada producto ocupa ~2 lineas), como corresponde a un
    rollo continuo: ni deja papel en blanco de mas ni corta contenido.
    """
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('producto')
    sucursal = Sucursal.objects.first()

    response = HttpResponse(content_type='application/pdf')
    nombre_archivo = venta.numero_ticket or f"VT-{venta.id:05d}"
    response['Content-Disposition'] = f'attachment; filename="ticket_{nombre_archivo}.pdf"'

    ancho_ticket = 58 * mm
    margen = 3 * mm
    ancho_util = ancho_ticket - (2 * margen)

    lineas_fijas = 14 + (3 if venta.cliente else 0)
    lineas_productos = len(detalles) * 2
    alto_estimado = (lineas_fijas + lineas_productos) * 3.3 * mm
    alto_ticket = max(alto_estimado, 60 * mm)

    doc = SimpleDocTemplate(
        response,
        pagesize=(ancho_ticket, alto_ticket),
        leftMargin=margen, rightMargin=margen,
        topMargin=margen, bottomMargin=margen,
    )

    base = getSampleStyleSheet()['Normal']
    estilo_titulo = ParagraphStyle('titulo', parent=base, alignment=1, fontName='Helvetica-Bold', fontSize=11, leading=13)
    estilo_centrado = ParagraphStyle('centrado', parent=base, alignment=1, fontSize=8, leading=10)
    estilo_normal = ParagraphStyle('normal_ticket', parent=base, fontSize=8, leading=10)
    estilo_pequeno = ParagraphStyle('pequeno_ticket', parent=base, fontSize=7, leading=9)

    def separador():
        return HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceBefore=2, spaceAfter=2)

    def fila_monto(etiqueta, valor, negritas=False):
        tabla = Table([[etiqueta, valor]], colWidths=[ancho_util * 0.6, ancho_util * 0.4])
        tabla.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold' if negritas else 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        return tabla

    elementos = []

    # ENCABEZADO (datos reales de la sucursal, no un texto fijo)
    nombre_negocio = sucursal.nombre if sucursal and sucursal.nombre else "Mi Negocio"
    elementos.append(Paragraph(nombre_negocio.upper(), estilo_titulo))
    if sucursal and sucursal.direccion:
        elementos.append(Paragraph(sucursal.direccion, estilo_centrado))
    if sucursal and sucursal.telefono:
        elementos.append(Paragraph(f"Tel: {sucursal.telefono}", estilo_centrado))
    elementos.append(Spacer(1, 2 * mm))

    elementos.append(Paragraph(f"Ticket: {venta.numero_ticket or venta.id}", estilo_normal))
    elementos.append(Paragraph(f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}", estilo_normal))
    if venta.vendedor:
        elementos.append(Paragraph(f"Atendio: {venta.vendedor.get_username()}", estilo_normal))

    if venta.cliente:
        elementos.append(separador())
        elementos.append(Paragraph(f"Cliente: {venta.cliente.nombre}", estilo_normal))
        if venta.cliente.telefono:
            elementos.append(Paragraph(f"Tel: {venta.cliente.telefono}", estilo_normal))

    elementos.append(separador())

    # PRODUCTOS: una linea con el nombre (puede envolver) y otra con
    # cantidad x precio / subtotal. Nada de columnas fijas por letra,
    # asi los nombres largos no rompen el ancho de 58mm.
    for d in detalles:
        subtotal = d.cantidad * d.precio
        elementos.append(Paragraph(d.producto.nombre, estilo_normal))
        elementos.append(fila_monto(f"{d.cantidad} x ${d.precio:.2f}", f"${subtotal:.2f}"))

    elementos.append(separador())

    elementos.append(fila_monto("TOTAL:", f"${venta.total:.2f}", negritas=True))
    if venta.monto_pagado is not None:
        elementos.append(fila_monto("Pago:", f"${venta.monto_pagado:.2f}"))
    if venta.cambio is not None:
        elementos.append(fila_monto("Cambio:", f"${venta.cambio:.2f}"))

    elementos.append(separador())
    mensaje_ticket = sucursal.mensaje_ticket if sucursal and sucursal.mensaje_ticket else "¡Gracias por su compra!"
    elementos.append(Paragraph(mensaje_ticket, estilo_centrado))
    elementos.append(Spacer(1, 3 * mm))

    doc.build(elementos)
    return response



@login_required
def imprimir_ticket(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta).select_related('producto')

    # Asumimos una sola sucursal por ahora (no hay selector de sucursal en el sistema)
    sucursal = Sucursal.objects.first()
    mensaje_ticket = sucursal.mensaje_ticket if sucursal and sucursal.mensaje_ticket else "¡Gracias por su compra!"

    # Calcula el precio total para cada producto
    for detalle in detalles:
        detalle.total_producto = detalle.cantidad * detalle.precio

    return render(request, "ticket.html", {
        "venta": venta,
        "detalles": detalles,
        "sucursal": sucursal,
        "mensaje_ticket": mensaje_ticket,
    })


logger = logging.getLogger(__name__)
@login_required
@require_http_methods(["GET"])
def api_buscar_por_codigo(request):
    codigo = request.GET.get('codigo', '').strip()
    if not codigo:
        return JsonResponse({'error': 'Código no proporcionado'}, status=400)

    try:
        cb = CodigoBarras.objects.select_related('producto').get(codigo=codigo)
        producto = cb.producto

        if producto.stock <= 0 and not producto.es_unico:
            return JsonResponse({'error': 'Producto sin stock'}, status=400)
        if producto.es_unico and cb.usado:
            return JsonResponse({'error': 'Este código ya fue utilizado'}, status=400)

        data = {
            'success': True,
            'id': producto.id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'es_unico': producto.es_unico,
            'codigo_barras_id': cb.id,
        }
        return JsonResponse(data)

    except CodigoBarras.DoesNotExist:
        logger.warning(f"Código no encontrado: {codigo}")
        return JsonResponse({'error': f'Código "{codigo}" no registrado'}, status=404)

    except Exception as e:
        logger.exception("Error inesperado en api_buscar_por_codigo")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)


def _filas_ventas(request):
    encabezados = ['Ticket', 'Fecha', 'Vendedor', 'Cliente', 'Ruta', 'Total', 'Monto pagado', 'Cambio']
    filas = []
    for venta in filtrar_ventas(request):
        filas.append([
            venta.numero_ticket or f"VT-{venta.id:05d}",
            venta.fecha.strftime('%d/%m/%Y %H:%M'),
            venta.vendedor.get_username() if venta.vendedor else '-',
            venta.cliente.nombre if venta.cliente else '-',
            venta.ruta.nombre if venta.ruta else '-',
            float(venta.total),
            float(venta.monto_pagado) if venta.monto_pagado is not None else '-',
            float(venta.cambio) if venta.cambio is not None else '-',
        ])
    return encabezados, filas


@login_required
def exportar_ventas_excel(request):
    encabezados, filas = _filas_ventas(request)
    return exportar_excel('ventas', encabezados, filas, titulo_hoja='Ventas')


@login_required
def exportar_ventas_pdf(request):
    encabezados, filas = _filas_ventas(request)
    return exportar_pdf('ventas', 'Listado de Ventas', encabezados, filas)