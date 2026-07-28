from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from caja.models import Caja, CorteCaja, Transaccion


class Command(BaseCommand):
    """Cierra automaticamente las cajas de dias anteriores que quedaron abiertas.

    Pensado para correr una vez al dia (por cron, despues de medianoche).
    No pide conteo fisico de efectivo: solo calcula lo que el sistema
    registro (ventas + ingresos/egresos manuales) y genera el corte. Si
    algun dia el negocio quiere volver a contar el efectivo a mano, eso
    se sigue pudiendo hacer con "Registrar corte" desde el panel, antes
    de que corra este comando.

    Uso tipico en crontab (ajustar rutas):
        0 0 * * * cd /ruta/al/proyecto && /ruta/al/venv/bin/python manage.py cerrar_cajas_del_dia
    """

    help = "Cierra y genera el corte automatico de las cajas abiertas de dias anteriores."

    def handle(self, *args, **options):
        hoy = timezone.localdate()
        cajas_pendientes = Caja.objects.filter(cerrado=False, fecha_apertura__date__lt=hoy)

        total_cerradas = 0
        for caja in cajas_pendientes:
            self._cerrar_caja(caja)
            total_cerradas += 1

        self.stdout.write(self.style.SUCCESS(
            f"{total_cerradas} caja(s) cerrada(s) automaticamente."
        ))

    def _cerrar_caja(self, caja):
        fecha_inicio = caja.fecha_apertura
        fecha_fin = timezone.now()

        transacciones = Transaccion.objects.filter(
            caja=caja,
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin,
        )
        ingresos = transacciones.filter(tipo='INGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
        egresos = transacciones.filter(tipo='EGRESO').aggregate(Sum('monto'))['monto__sum'] or 0
        saldo_final = (caja.saldo_inicial or 0) + ingresos - egresos

        corte = CorteCaja.objects.create(
            caja=caja,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            saldo_inicial=caja.saldo_inicial,
            saldo_final=saldo_final,
            usuario_cierre=caja.usuario_apertura,
            comentario='Cierre automatico de fin de dia.',
        )
        corte.transacciones.set(transacciones)
        corte.calcular_totales()

        caja.cerrar_caja(usuario=caja.usuario_apertura)
