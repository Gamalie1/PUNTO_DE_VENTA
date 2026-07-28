from django.db import models
from django.utils import timezone  # Asegúrate de importar timezone

from django.conf import settings

# Create your models here.
class Caja(models.Model):
    nombre = models.CharField(max_length=150)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    usuario_apertura = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="cajas_abiertas")
    usuario_cierre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="cajas_cerradas")
    cerrado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} - Saldo Actual: ${self.saldo_actual}"

    def abrir_caja(self, saldo_inicial):
        self.saldo_inicial = saldo_inicial
        self.saldo_actual = saldo_inicial
        self.save()

    def cerrar_caja(self, usuario=None):
        """Cierra la caja, marca como cerrada, guarda la fecha de cierre y el usuario que cerró la caja."""
        self.cerrado = True
        self.fecha_cierre = timezone.now()  # Usamos timezone.now() para obtener la fecha y hora actuales
        if usuario:
            self.usuario_cierre = usuario  # Asignar el usuario que cierra la caja
        self.save()
    
    def agregar_ingreso(self, monto):
        self.saldo_actual += monto
        self.save()

    def agregar_egreso(self, monto):
        self.saldo_actual -= monto
        self.save()

class Transaccion(models.Model):
    CAJA_OPERACIONES = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]
    METODOS_PAGO = [
        ('EFECTIVO', 'Efectivo'),
        ('TARJETA', 'Tarjeta'),
        ('TRANSFERENCIA', 'Transferencia'),
    ]
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name="transacciones")
    tipo = models.CharField(max_length=7, choices=CAJA_OPERACIONES)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='EFECTIVO')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    venta = models.ForeignKey('ventas.Venta', on_delete=models.SET_NULL, null=True, blank=True, related_name='transacciones')

    class Meta:
        indexes = [
            # Los cortes de caja (manuales y el cierre automatico) filtran
            # transacciones por caja + rango de fecha en cada corte.
            models.Index(fields=['fecha']),
            models.Index(fields=['caja', 'fecha']),
        ]

    def __str__(self):
        return f"{self.tipo} - ${self.monto} ({self.fecha})"


class CorteCaja(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='cortes')
    transacciones = models.ManyToManyField(Transaccion, blank=True)
    # Periodo que cubre el corte (desde la apertura de la caja hasta el momento del corte).
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    ingresos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    egresos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2)
     # 🧾 Auditoría
    monto_fisico = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    diferencia = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # 👤 Usuario
    usuario_cierre = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_corte = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)  # Comentarios adicionales

    class Meta:
        # Sin esto, CorteCajaListView (que pagina) emite
        # UnorderedObjectListWarning y puede repetir/saltar filas entre
        # paginas porque Postgres no garantiza el orden sin ORDER BY.
        ordering = ['-fecha_corte']
        indexes = [
            # Se consulta en cada intento de corte para evitar duplicados
            # del mismo dia (fecha_corte__date=hoy).
            models.Index(fields=['fecha_corte']),
        ]

    def __str__(self):
        return f"Corte de Caja - {self.caja.nombre} - {self.fecha_corte}"

   # 🔥 CÁLCULO AUTOMÁTICO (CLAVE)
    def calcular_totales(self):
        ingresos = self.transacciones.filter(tipo='INGRESO').aggregate(
            total=models.Sum('monto')
        )['total'] or 0

        egresos = self.transacciones.filter(tipo='EGRESO').aggregate(
            total=models.Sum('monto')
        )['total'] or 0

        self.ingresos = ingresos
        self.egresos = egresos
        self.saldo_final = self.saldo_inicial + ingresos - egresos

        self.save()

    # 🔍 DIFERENCIA (AUDITORÍA)
    def calcular_diferencia(self):
        if self.monto_fisico is not None:
            self.diferencia = self.monto_fisico - self.saldo_final
            self.save()

    # 📄 REPORTE
    def generar_reporte(self):
        return {
            'caja': self.caja.nombre,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'saldo_inicial': self.saldo_inicial,
            'ingresos': self.ingresos,
            'egresos': self.egresos,
            'saldo_final': self.saldo_final,
            'monto_fisico': self.monto_fisico,
            'diferencia': self.diferencia,
            'usuario': self.usuario_cierre,
            'comentario': self.comentario,
        }
