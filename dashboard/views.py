from django.shortcuts import render
from django.http import HttpResponse
import pandas as pd
from io import BytesIO
from .models import IngresoMensual
from .forms import MovimientoForm
from decimal import Decimal
from datetime import datetime

# --- CONSULTAR REGISTROS Y ORDENAR CORRECTAMENTE ---
registros = list(IngresoMensual.objects.all())

# Convertir 'Jan-25' → datetime(2025, 1, 1)
def parse_periodo(p):
    try:
        return datetime.strptime(p, "%b-%y")
    except Exception:
        return datetime.max  # por si hay errores

registros.sort(key=lambda r: parse_periodo(r.periodo))

periodos = sorted(
    IngresoMensual.objects.values_list("periodo", flat=True).distinct(),
    key=lambda p: parse_periodo(p)
)


def index(request):
    form = MovimientoForm(request.POST or None)
    mensaje = ""

    # --- FORMULARIO PARA AÑADIR MOVIMIENTOS ---
    if request.method == "POST" and "añadir" in request.POST and form.is_valid():
        periodo_existente = form.cleaned_data["periodo"].periodo if form.cleaned_data["periodo"] else None
        nuevo_periodo = form.cleaned_data["nuevo_periodo"]
        columna = form.cleaned_data["columna"]
        monto = Decimal(form.cleaned_data["monto"])

        # Determinar periodo final
        periodo_final = nuevo_periodo.strip() if nuevo_periodo else periodo_existente

        ingreso, _ = IngresoMensual.objects.get_or_create(periodo=periodo_final)
        valor_actual = getattr(ingreso, columna, 0) or 0
        setattr(ingreso, columna, valor_actual + monto)

        # Actualizar ingresos netos automáticamente
        ingreso.ingresos_netos_mantenimiento = (
            (ingreso.ingresos_mantenimiento or 0)
            - (ingreso.dppp or 0)
        )

        ingreso.save()
        mensaje = f"✅ Se añadió {monto:,.2f} a '{columna}' en {periodo_final}"

    # --- GENERAR REPORTE EXCEL ---
    if request.method == "POST" and "generar_reporte" in request.POST:
        inicio = request.POST.get("inicio")
        fin = request.POST.get("fin")

        data = IngresoMensual.objects.filter(periodo__gte=inicio, periodo__lte=fin).order_by("periodo")
        df = pd.DataFrame(list(data.values()))
        if df.empty:
            return HttpResponse("No hay datos para ese rango de periodos.")

        # Cálculo de Total y Diferencia
        df["Total"] = (
            df["ingresos_mantenimiento"] + df["dppp"] + df["ingresos_netos_mantenimiento"] +
            df["ingresos_cuota_extraordinaria"] + df["cuota_ordinaria_retroactiva"] +
            df["revision_csau"] + df["depositos_garantia_obra"] +
            df["ingresos_intereses_cuotas"] + df["ingresos_rendimiento_inversiones"] +
            df["sanciones"] + df["recuperacion_seguro_danios"] +
            df["recuperacion_gastos_cobranza"] + df["depositos_no_identificados"]
        )

        df["diferencia_ingresos_fac_vs_cobrados"] = df["Total"] - df["ingresos_reales_vs_fact"]
        df = df.round(2)

        # Fila total general
        totales = df.select_dtypes(include=["number"]).sum()
        totales["periodo"] = "TOTAL"
        df = pd.concat([df, pd.DataFrame([totales])], ignore_index=True)

        # Exportar a Excel
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="reporte_finanzas.xlsx"'
        return response

    # --- CONSULTAR REGISTROS Y REDONDEAR ---
    registros = IngresoMensual.objects.all().order_by("periodo")
    periodos = IngresoMensual.objects.values_list("periodo", flat=True).distinct().order_by("periodo")

    campos_numericos = [
        "ingresos_mantenimiento", "dppp", "ingresos_netos_mantenimiento",
        "ingresos_cuota_extraordinaria", "cuota_ordinaria_retroactiva",
        "revision_csau", "depositos_garantia_obra", "ingresos_intereses_cuotas",
        "ingresos_rendimiento_inversiones", "sanciones", "recuperacion_seguro_danios",
        "recuperacion_gastos_cobranza", "depositos_no_identificados",
        "total", "ingresos_reales_vs_fact", "diferencia_ingresos_fac_vs_cobrados"
    ]

    for r in registros:
        for campo in campos_numericos:
            valor = getattr(r, campo, None)
            if isinstance(valor, (int, float)):
                setattr(r, campo, round(valor, 2))

    return render(
        request,
        "finanzas/index.html",
        {
            "form": form,
            "mensaje": mensaje,
            "registros": registros,
            "periodos": periodos,
        },
    )
