from django.db import models
from django.utils import timezone

class IngresoMensual(models.Model):
    periodo = models.CharField(max_length=10)  # Ej: "Jan-25"
    ingresos_mantenimiento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dppp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ingresos_netos_mantenimiento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ingresos_cuota_extraordinaria = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cuota_ordinaria_retroactiva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    revision_csau = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depositos_garantia_obra = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ingresos_intereses_cuotas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ingresos_rendimiento_inversiones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sanciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recuperacion_seguro_danios = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recuperacion_gastos_cobranza = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depositos_no_identificados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ingresos_reales_vs_fact = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    diferencia_ingresos_fac_vs_cobrados = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)

    def total(self):
        campos = [
            self.ingresos_netos_mantenimiento,
            self.ingresos_cuota_extraordinaria, self.cuota_ordinaria_retroactiva,
            self.revision_csau, self.depositos_garantia_obra,
            self.ingresos_intereses_cuotas, self.ingresos_rendimiento_inversiones,
            self.sanciones, self.recuperacion_seguro_danios,
            self.recuperacion_gastos_cobranza, self.depositos_no_identificados
        ]
        return sum(campos)

    def save(self, *args, **kwargs):
        # Calcular diferencia automáticamente
        self.diferencia_ingresos_fac_vs_cobrados = self.total() - self.ingresos_reales_vs_fact
        super().save(*args, **kwargs)

    def __str__(self):
        return self.periodo

class MovimientoLog(models.Model):
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=20)  # "añadir", "editar", "eliminar"
    periodo = models.CharField(max_length=20, null=True, blank=True)
    columna = models.CharField(max_length=50, null=True, blank=True)
    monto = models.FloatField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} - {self.tipo} ({self.columna})"