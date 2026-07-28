from django.utils import timezone

from .models import Caja


def obtener_o_abrir_caja_del_dia(usuario):
    """Devuelve la caja abierta hoy para este usuario, o la crea si no existe.

    Reemplaza el flujo anterior donde el cajero tenia que llenar un
    formulario (nombre + saldo inicial) antes de poder vender. Ahora la
    caja se abre sola, en silencio, con la primera venta del dia de cada
    vendedor. El cierre lo hace el comando `cerrar_cajas_del_dia`
    (pensado para correr por cron a medianoche).
    """
    hoy = timezone.localdate()
    caja = Caja.objects.filter(
        usuario_apertura=usuario,
        cerrado=False,
        fecha_apertura__date=hoy,
    ).first()
    if caja:
        return caja

    return Caja.objects.create(
        nombre=f"Caja {usuario.get_username()} - {hoy.strftime('%d/%m/%Y')}",
        saldo_inicial=0,
        saldo_actual=0,
        usuario_apertura=usuario,
    )
