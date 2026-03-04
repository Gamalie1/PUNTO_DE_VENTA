from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from inventario.models import Producto
from .models import Venta, DetalleVenta
from django.db import transaction

# Create your views here.

@login_required
def punto_venta(request):
    productos = Producto.objects.all()

    if request.method == "POST":
        carrito = request.session.get("carrito", {})
        if not carrito:
            return redirect("punto_venta")

        with transaction.atomic():
            total = 0
            venta = Venta.objects.create(
                vendedor=request.user,
                total=0
            )

            for producto_id, item in carrito.items():
                producto = Producto.objects.get(id=producto_id)
                cantidad = item["cantidad"]

                if producto.stock < cantidad:
                    continue

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

            venta.total = total
            venta.save()

        request.session["carrito"] = {}
        return redirect("punto_venta")

    return render(request, "punto_venta.html", {"productos": productos})