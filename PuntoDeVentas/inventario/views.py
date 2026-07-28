from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from usuarios.permissions import rol_required
from .models import Producto, CodigoBarras, HistorialStock
from .forms import ProductoForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from django.contrib import messages
import uuid

# Create your views here.
@login_required
def lista_productos(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')

    context = {
        'productos': productos,
        'total_productos': productos.count(),
        'con_stock': productos.filter(stock__gt=0).count(),
        'sin_stock': productos.filter(stock=0).count(),
    }
    return render(request, 'lista_productos.html', context)


@rol_required('ADMIN', 'ALMACEN')
def registrar_producto(request):
    if request.method == 'POST':
        # Si el formulario es enviado, procesamos los datos
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            # Guardamos el producto
            producto = form.save()

            # Si el producto es único, generamos los códigos de barras
            producto.generar_codigos_barras()

            return redirect('lista_productos')  # Redirige a la lista de productos después de guardar
    else:
        # Si es un GET, simplemente mostramos el formulario vacío
        form = ProductoForm()

    return render(request, 'crear_producto.html', {'form': form})

# Vista para editar producto
@rol_required('ADMIN', 'ALMACEN')
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    
    # Obtener el historial de movimientos para este producto
    historial_stock = HistorialStock.objects.filter(producto=producto).order_by('-fecha')
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'editar_producto.html', {'form': form, 'producto': producto, 'historial_stock': historial_stock,})


# Vista para eliminar producto
@rol_required('ADMIN', 'ALMACEN')
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.delete()
    messages.success(request, 'Producto eliminado correctamente.')
    return redirect('lista_productos')

def dibujar_etiqueta(c, x, y, producto, codigo_barras, ancho=90*mm, alto=35*mm):
    """Dibuja una etiqueta con la información del producto y su código de barras"""
    c.roundRect(x, y, ancho, alto, 4, stroke=1, fill=0)

    # Nombre del producto
    nombre = producto.nombre[:28]
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 4*mm, y + alto - 7*mm, nombre)

    # Precio
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 4*mm, y + alto - 14*mm, f"Precio: ${producto.precio}")

    # *** CÓDIGO DE BARRAS MEJORADO ***
    # Usar barWidth en milímetros (0.3 mm es un buen grosor)
    # barHeight de 12 mm asegura que sea fácil de escanear
    bc = code128.Code128(codigo_barras,
                         barHeight=12*mm,   # más alto = mejor lectura
                         barWidth=0.3*mm)   # grosor de línea en mm
    # Dibujar en coordenadas ajustadas (dejando márgenes)
    bc_x = x + 4*mm
    bc_y = y + 5*mm   # espacio suficiente para el texto inferior
    bc.drawOn(c, bc_x, bc_y)

    # Texto legible del código (opcional pero útil)
    c.setFont("Helvetica", 6)
    c.drawString(x + 4*mm, y + 2*mm, codigo_barras[:20])  # mostrar primeros 20 caracteres
    

@login_required
def producto_etiqueta_pdf(request, pk):
    # Obtener el producto que se va a etiquetar
    producto = get_object_or_404(Producto, pk=pk)

    # Respuesta en PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="etiqueta_{producto.id}.pdf"'

    # Crear el lienzo del PDF
    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Definir las posiciones de las etiquetas
    x = 20 * mm
    y = height - 60 * mm
    ancho_etiqueta = 90 * mm  # Ancho ajustado para 2 columnas
    alto_etiqueta = 35 * mm
    espacio_x = 5 * mm
    espacio_y = 5 * mm

    # Número de columnas y filas por página
    max_columnas = 2  # Cambiado a 2 columnas
    max_filas = 6     # Ajustado para más filas
    col = 0
    fila = 0

    # Generar tantas etiquetas como el stock del producto
    if producto.es_unico:  # Producto único, generar tantas etiquetas como unidades
        codigos_barras = producto.codigos_barras.all()  # Obtener los códigos de barras únicos de la base de datos
        for idx, cb in enumerate(codigos_barras):
            # Calcular la posición para cada código de barras
            x_pos = x + col * (ancho_etiqueta + espacio_x)
            y_pos = y - fila * (alto_etiqueta + espacio_y)

            # Dibujar la etiqueta para este código de barras
            dibujar_etiqueta(c, x_pos, y_pos, producto, cb.codigo)

            # Ajustar la posición para la siguiente etiqueta
            col += 1
            if col >= max_columnas:  # Si alcanzamos el límite de columnas, pasamos a la siguiente fila
                col = 0
                fila += 1
                if fila >= max_filas:  # Si alcanzamos el límite de filas, pasamos a una nueva página
                    c.showPage()  # Crear una nueva página
                    fila = 0
                    x = 20 * mm
                    y = height - 60 * mm
    else:  # Producto no único, generar tantas etiquetas con el mismo código de barras
        for idx in range(producto.stock):  # Generar el mismo código de barras varias veces si no es único
            # Calcular la posición para la etiqueta
            x_pos = x + col * (ancho_etiqueta + espacio_x)
            y_pos = y - fila * (alto_etiqueta + espacio_y)

            # Dibujar la etiqueta para este código de barras
            dibujar_etiqueta(c, x_pos, y_pos, producto, producto.codigos_barras.first().codigo)

            # Ajustar la posición para la siguiente etiqueta
            col += 1
            if col >= max_columnas:  # Si alcanzamos el límite de columnas, pasamos a la siguiente fila
                col = 0
                fila += 1
                if fila >= max_filas:  # Si alcanzamos el límite de filas, pasamos a una nueva página
                    c.showPage()  # Crear una nueva página
                    fila = 0
                    x = 20 * mm
                    y = height - 60 * mm

    # Terminar y devolver el PDF
    c.showPage()
    c.save()

    return response




@rol_required('ADMIN', 'ALMACEN')
def agregar_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 0))
        comentario = request.POST.get('comentario', '')
        tipo_cambio = request.POST.get('tipo_cambio', 'añadido')  # "añadido" o "vendido"

        if cantidad > 0:
            if tipo_cambio == 'añadido':
                # Agregar stock
                producto.stock += cantidad
                producto.save()

                # Si el producto es único, generamos códigos de barras para las unidades adicionales
                if producto.es_unico:
                    for _ in range(cantidad):
                        CodigoBarras.objects.create(
                            producto=producto,
                            codigo=str(uuid.uuid4())  # Genera un nuevo código único
                        )

                # Registrar el cambio en el historial de stock
                HistorialStock.objects.create(
                    producto=producto,
                    cantidad=cantidad,
                    tipo_cambio='añadido',
                    comentario=comentario
                )

                messages.success(request, f'Se agregaron {cantidad} unidades a {producto.nombre}.')
            elif tipo_cambio == 'vendido' and producto.stock >= cantidad:
                # Reducir stock (por ejemplo, cuando se hace una venta)
                producto.stock -= cantidad
                producto.save()

                # Registrar la reducción en el historial de stock
                HistorialStock.objects.create(
                    producto=producto,
                    cantidad=cantidad,
                    tipo_cambio='vendido',
                    comentario=comentario
                )

                # Eliminar los códigos de barras correspondientes si el stock se ha reducido
                
                codigos_a_eliminar = CodigoBarras.objects.filter(producto=producto)[:cantidad]
                # Eliminar sin usar limit/offset
                CodigoBarras.objects.filter(id__in=[codigo.id for codigo in codigos_a_eliminar]).delete()

                messages.success(request, f'Se redujeron {cantidad} unidades de {producto.nombre}.')
            elif tipo_cambio == 'ajuste' and producto.stock >= cantidad:
                # Reducción por ajuste de inventario
                producto.stock -= cantidad
                producto.save()

                # Registrar ajuste en el historial de stock
                HistorialStock.objects.create(
                    producto=producto,
                    cantidad=cantidad,
                    tipo_cambio='ajuste',
                    comentario=comentario
                )

                # Eliminar los códigos de barras correspondientes si el stock se ha ajustado
                codigos_a_eliminar = CodigoBarras.objects.filter(producto=producto)[:cantidad]
                # Eliminar sin usar limit/offset
                CodigoBarras.objects.filter(id__in=[codigo.id for codigo in codigos_a_eliminar]).delete()

                messages.success(request, f'Ajuste: Se redujeron {cantidad} unidades de {producto.nombre}.')
            else:
                messages.error(request, 'No hay suficiente stock para esta operación.')

        else:
            messages.error(request, 'La cantidad debe ser mayor que 0.')

    return redirect('editar_producto', pk=producto.pk)