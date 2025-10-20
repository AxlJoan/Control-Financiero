from django import forms
from .models import IngresoMensual

class MovimientoForm(forms.Form):
    periodo = forms.ModelChoiceField(
        queryset=IngresoMensual.objects.all(),
        required=False,
        empty_label="Seleccionar periodo existente",
        to_field_name="periodo",
        label="Periodo existente"
    )
    nuevo_periodo = forms.CharField(required=False, max_length=10, help_text="Ej: Jan-25")
    columna = forms.ChoiceField(choices=[
        ("ingresos_mantenimiento", "Ingresos x Mantenimiento"),
        ("dppp", "DPPP"),
        ("ingresos_netos_mantenimiento", "Ingresos Netos por Mantenimiento"),
        ("ingresos_cuota_extraordinaria", "Ingreso x Cuota Extraordinaria"),
        ("cuota_ordinaria_retroactiva", "Cuota Ordinaria Retroactiva"),
        ("revision_csau", "Revisión CSAU"),
        ("depositos_garantia_obra", "Depósitos en Garantía de Obra"),
        ("ingresos_intereses_cuotas", "Ingresos x Intereses de Cuotas"),
        ("ingresos_rendimiento_inversiones", "Ingresos por Rendimiento de Inversiones"),
        ("sanciones", "Sanciones"),
        ("recuperacion_seguro_danios", "Recuperación de Seguro/Daños"),
        ("recuperacion_gastos_cobranza", "Recuperación de gastos por Cobranza vía legal"),
        ("depositos_no_identificados", "Depósitos no identificados"),
        ("ingresos_reales_vs_fact", "Ingresos reales vs fact"),
    ])
    monto = forms.DecimalField(max_digits=12, decimal_places=2)

