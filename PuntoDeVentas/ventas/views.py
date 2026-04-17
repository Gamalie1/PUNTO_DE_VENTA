from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from inventario.models import Producto, CodigoBarras
from .models import Venta, DetalleVenta
from sucursal.models import Sucursal
from django.db import transaction
from caja.models import Caja
import json
from django.views.generic import ListView
from django.views.generic import DetailView
from decimal import Decimal
from django.http import JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image,TableStyle
from reportlab.lib.pagesizes import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import os
from django.conf import settings
from django.contrib.staticfiles import finders
from reportlab.platypus import HRFlowable
from datetime import datetime
from django.utils.dateparse import parse_date
from clientes.models import Cliente
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from caja.models import Transaccion
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

@login_required
def punto_venta(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()
    caja_abierta = Caja.objects.filter(cerrado=False).first()

    if not caja_abierta:
        return render(request, "punto_venta.html", {
            "productos": productos,
            "clientes": clientes,
            "mensaje_error": "No hay ninguna caja abierta."
        })

    if request.method == "POST":
        carrito_json = request.POST.get("carrito")
        monto_pagado = request.POST.get("monto_pagado")
        cambio = request.POST.get("cambio")
        cliente_id = request.POST.get("cliente_id")

        if not carrito_json:
            return render(request, "punto_venta.html", {...})

        carrito = json.loads(carrito_json)

        with transaction.atomic():
            total = 0
            venta = Venta.objects.create(
                vendedor=request.user,
                total=0,
                caja=caja_abierta  # 👈 Asignar caja
            )

            if cliente_id:
                try:
                    venta.cliente = Cliente.objects.get(id=cliente_id)
                except:
                    pass

            # Procesar detalles
            for producto_id, item in carrito.items():
                producto = Producto.objects.get(id=producto_id)
                cantidad = item["cantidad"]
                subtotal = producto.precio * cantidad
                total += subtotal

                DetalleVenta.objects.create(
                    venta=venta,
                    producto=producto,
                    cantidad=cantidad,
                    precio=producto.precio
                )
                producto.stock -= cantidad
                producto.save()

            if total == 0:
                venta.delete()
                return render(request, "punto_venta.html", {"mensaje_error": "No hay stock suficiente"})

            venta.total = total
            venta.monto_pagado = Decimal(monto_pagado) if monto_pagado else None
            venta.cambio = Decimal(cambio) if cambio else None
            venta.save()

            # ✅ CREAR TRANSACCIÓN DE INGRESO
            Transaccion.objects.create(
                caja=caja_abierta,
                tipo='INGRESO',
                metodo_pago='EFECTIVO',
                monto=total,
                descripcion=f"Venta #{venta.numero_ticket or venta.id}",
                venta=venta
            )

            return render(request, "punto_venta.html", {
                "productos": productos,
                "clientes": clientes,
                "success": True,
                "venta_id": venta.id
            })

    return render(request, "punto_venta.html", {"productos": productos, "clientes": clientes})

class VentaListView(LoginRequiredMixin, ListView):
    model = Venta
    template_name = 'venta_list.html'
    context_object_name = 'ventas'
    paginate_by = 20

    def get_queryset(self):
        # Base: ordenar por fecha descendente
        queryset = super().get_queryset().order_by('-fecha')

        # Filtrar según el rol del usuario actual
        user = self.request.user
        if user.rol != 'ADMIN':
            # Si es cajero o almacén, solo sus propias ventas
            queryset = queryset.filter(vendedor=user)  # Cambia 'usuario' por el campo real

        # Filtro por número de ticket (si existe)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(numero_ticket__icontains=search)

        # Filtro por rango de fechas
        fecha_range = self.request.GET.get('fecha')
        if fecha_range:
            partes = fecha_range.split(' - ')
            if len(partes) == 2:
                fecha_desde = parse_date(partes[0])
                fecha_hasta = parse_date(partes[1])
                if fecha_desde and fecha_hasta:
                    fecha_hasta = datetime.combine(fecha_hasta, datetime.max.time())
                    queryset = queryset.filter(fecha__range=(fecha_desde, fecha_hasta))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['fecha'] = self.request.GET.get('fecha', '')
        return context
    
class VentaDetailView(DetailView):
    model = Venta
    template_name = 'venta_detail.html'
    context_object_name = 'venta'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar los detalles de la venta a la variable de contexto
        venta = self.get_object()
        context['detalles'] = venta.detalles.all()  # Obtener los productos de la venta
        return context
    
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

def descargar_ticket(request, venta_id):
    venta = Venta.objects.get(id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{venta.id}.pdf"'

    # Márgenes más ajustados para simular ticket
    doc = SimpleDocTemplate(response, pagesize=letter,
                            rightMargin=0.6*inch, leftMargin=0.6*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    estilo_normal = styles['Normal']
    estilo_titulo = styles['Title']
    estilo_negrita = ParagraphStyle(
        'negrita',
        parent=estilo_normal,
        fontName='Helvetica-Bold',
        fontSize=10
    )
    estilo_pequeno = ParagraphStyle(
        'pequeno',
        parent=estilo_normal,
        fontSize=8
    )

    # Ajustes generales
    estilo_normal.fontSize = 9
    estilo_titulo.fontSize = 14
    estilo_titulo.alignment = 1  # centrado

    elementos = []

    # LOGO + TÍTULO
    logo_path = finders.find('dist/img/AdminLTELogo.png')
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path, width=40, height=40)
    else:
        logo = ""

    titulo = Paragraph("<b>Purificadora</b>", estilo_titulo)

    header = Table(
        [[logo, titulo]],
        colWidths=[50, 150]
    )
    header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    elementos.append(header)
    elementos.append(Spacer(1, 10))

    # DATOS DEL TICKET
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Paragraph(f"<b>Ticket:</b> #{venta.id}", estilo_normal))
    elementos.append(Paragraph(f"<b>Fecha:</b> {venta.fecha.strftime('%d/%m/%Y %H:%M')}", estilo_normal))

    # CLIENTE (si existe)
    if venta.cliente:
        elementos.append(Spacer(1, 5))
        elementos.append(Paragraph("<b>Cliente:</b>", estilo_negrita))
        cliente_info = [f"Nombre: {venta.cliente.nombre}"]
        if venta.cliente.telefono:
            cliente_info.append(f"Teléfono: {venta.cliente.telefono}")
        if venta.cliente.direccion:
            cliente_info.append(f"Dirección: {venta.cliente.direccion}")
        for line in cliente_info:
            elementos.append(Paragraph(line, estilo_normal))
        elementos.append(Spacer(1, 5))

    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Spacer(1, 5))

    # TABLA DE PRODUCTOS
    data = [["Cant.", "Producto", "Precio Unit.", "Subtotal"]]
    for d in detalles:
        subtotal = d.cantidad * d.precio
        data.append([
            f"{d.cantidad}",
            d.producto.nombre,
            f"${d.precio:.2f}",
            f"${subtotal:.2f}"
        ])

    # Anchos de columna (ajustables)
    col_widths = [40, 180, 80, 80]
    tabla_productos = Table(data, colWidths=col_widths)
    tabla_productos.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('ALIGN', (2,1), (3,-1), 'RIGHT'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 10))

    # RESUMEN (subtotal, total, pago)
    resumen_data = [
        ["Subtotal:", f"${venta.total:.2f}"],
        ["Descuento:", "$0.00"],
        ["Total a pagar:", f"${venta.total:.2f}"],
        ["", ""],
        ["Efectivo recibido:", f"${venta.monto_pagado:.2f}" if venta.monto_pagado else "$0.00"],
        ["Cambio:", f"${venta.cambio:.2f}" if venta.cambio else "$0.00"],
    ]

    tabla_resumen = Table(resumen_data, colWidths=[150, 100])
    tabla_resumen.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LINEABOVE', (0,2), (-1,2), 0.5, colors.grey),
        ('LINEBELOW', (0,2), (-1,2), 0.5, colors.grey),
        ('LINEABOVE', (0,4), (-1,4), 0.5, colors.grey),
        ('LINEBELOW', (0,4), (-1,4), 0.5, colors.grey),
        ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
        ('FONTNAME', (0,4), (-1,4), 'Helvetica-Bold'),
    ]))

    # Colocamos la tabla de resumen centrada después de la tabla de productos
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 20))

    # MENSAJE FINAL
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elementos.append(Spacer(1, 5))
    elementos.append(Paragraph("¡Gracias por su compra!", estilo_negrita))
    elementos.append(Paragraph("Vuelva pronto", estilo_pequeno))

    doc.build(elementos)
    return response



def imprimir_ticket(request, venta_id):
    venta = Venta.objects.get(id=venta_id)
    detalles = DetalleVenta.objects.filter(venta=venta)
    
    # Obtener el mensaje del ticket de la sucursal
    sucursal = Sucursal.objects.first()  # Asumimos que solo tienes una sucursal
    mensaje_ticket = sucursal.mensaje_ticket if sucursal else "Gracias por su compra."

    # Calcula el precio total para cada producto
    for detalle in detalles:
        detalle.total_producto = detalle.cantidad * detalle.precio

    return render(request, "ticket.html", {
        "venta": venta,
        "detalles": detalles,
        "mensaje_ticket": mensaje_ticket  # Pasamos el mensaje del ticket
    })