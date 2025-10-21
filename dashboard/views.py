import json
import pandas as pd
from io import BytesIO
from decimal import Decimal
from openpyxl import Workbook
from datetime import datetime
from .forms import MovimientoForm
from django.contrib import messages
from django.http import HttpResponse
from django.forms.models import model_to_dict
from .models import IngresoMensual, MovimientoLog
from django.shortcuts import render, redirect, get_object_or_404
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# --- CONSULTAR REGISTROS Y ORDENAR CORRECTAMENTE ---
registros = list(IngresoMensual.objects.all().values())

def index(request):
    form = MovimientoForm(request.POST or None)
    mensaje = ""

    # --- AÑADIR MOVIMIENTO ---
    if request.method == "POST" and "añadir" in request.POST and form.is_valid():
        periodo_existente = form.cleaned_data["periodo"].periodo if form.cleaned_data["periodo"] else None
        nuevo_periodo = form.cleaned_data["nuevo_periodo"]
        columna = form.cleaned_data["columna"]
        monto = Decimal(form.cleaned_data["monto"])

        periodo_final = nuevo_periodo.strip() if nuevo_periodo else periodo_existente
        ingreso, _ = IngresoMensual.objects.get_or_create(periodo=periodo_final)
        valor_actual = getattr(ingreso, columna, 0) or 0
        setattr(ingreso, columna, valor_actual + monto)

        ingreso.ingresos_netos_mantenimiento = (
            (ingreso.ingresos_mantenimiento or 0) - (ingreso.dppp or 0)
        )
        ingreso.save()

        # --- Registrar log ---
        MovimientoLog.objects.create(
            tipo="añadir",
            periodo=periodo_final,
            columna=columna,
            monto=monto,
            observaciones=f"Añadido {monto} a '{columna}' en {periodo_final}"
        )

        mensaje = f"✅ Se añadió {monto:,.2f} a '{columna}' en {periodo_final}"

    # --- ELIMINAR REGISTRO ---
    if request.method == "POST" and "eliminar" in request.POST:
        id_registro = request.POST.get("id_registro")
        ingreso = get_object_or_404(IngresoMensual, id=id_registro)
        MovimientoLog.objects.create(
            tipo="eliminar",
            periodo=ingreso.periodo,
            columna="N/A",
            monto=0,
            observaciones=f"Eliminado registro ID {id_registro} ({ingreso.periodo})"
        )
        ingreso.delete()
        mensaje = f"Registro {id_registro} eliminado correctamente."

    # --- EDITAR REGISTRO ---
    if request.method == "POST" and "editar" in request.POST:
        id_registro = request.POST.get("id_registro")
        columna = request.POST.get("columna")
        nuevo_valor = Decimal(request.POST.get("nuevo_valor", 0))
        ingreso = get_object_or_404(IngresoMensual, id=id_registro)
        setattr(ingreso, columna, nuevo_valor)

        ingreso.ingresos_netos_mantenimiento = (
            (ingreso.ingresos_mantenimiento or 0) - (ingreso.dppp or 0)
        )
        ingreso.save()

        # --- Registrar log ---
        MovimientoLog.objects.create(
            tipo="editar",
            periodo=ingreso.periodo,
            columna=columna,
            monto=nuevo_valor,
            observaciones=f"Editado '{columna}' en {ingreso.periodo}"
        )

        mensaje = f"Registro {id_registro} actualizado correctamente."

    # --- GENERAR REPORTE ---
    if request.method == "POST" and "generar_reporte" in request.POST:
        inicio = request.POST.get("inicio")
        fin = request.POST.get("fin")
        try:
            inicio_obj = IngresoMensual.objects.get(periodo=inicio)
            fin_obj = IngresoMensual.objects.get(periodo=fin)
        except IngresoMensual.DoesNotExist:
            return HttpResponse("Alguno de los periodos no existe.")

        data = IngresoMensual.objects.filter(
            id__gte=inicio_obj.id,
            id__lte=fin_obj.id
        ).order_by("id")
        if not data.exists():
            return HttpResponse("No hay datos para ese rango.")

        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte Financiero"
        headers = [
            "Periodo", "Ingresos x  Mantenimiento", "DPPP", "Ingresos Netos por Mantenimiento", "Ingreso x Cuota Extraordinaria",
            "Cuota ordinaria retroactiva", "Revision CSAU", "Depósitos en garantia de obra", "Ingresos x Intereses de Cuotas",
            "Ingresos por Rendimiento de Inversiones", "Sanciones", "Recuperación de Seguro/daños", "Recuperación de gastos por Cobranza via legal", "Depositos no identificados",
            "Total", "Ingresos reales vs fact", "Diferencia de ingresos fac vs cobrados", "Observaciones"
        ]
        ws.append(headers)
        header_fill = PatternFill("solid", fgColor="1e3a8a")
        header_font = Font(color="FFFFFF", bold=True)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r in data:
            ws.append([
                r.periodo, r.ingresos_mantenimiento, r.dppp, r.ingresos_netos_mantenimiento,
                r.ingresos_cuota_extraordinaria, r.cuota_ordinaria_retroactiva,
                r.revision_csau, r.depositos_garantia_obra,
                r.ingresos_intereses_cuotas, r.ingresos_rendimiento_inversiones,
                r.sanciones, r.recuperacion_seguro_danios,
                r.recuperacion_gastos_cobranza, r.depositos_no_identificados,
                r.total(), r.ingresos_reales_vs_fact, r.diferencia_ingresos_fac_vs_cobrados
            ])

        # Fila de totales
        total_row = ["TOTAL"]
        for col in range(2, len(headers) + 1):
            col_letter = ws.cell(row=1, column=col).column_letter
            total_row.append(f"=SUM({col_letter}2:{col_letter}{len(data) + 1})")
        ws.append(total_row)
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="eab308")

        border = Border(
            left=Side(style="thin", color="CCCCCC"),
            right=Side(style="thin", color="CCCCCC"),
            top=Side(style="thin", color="CCCCCC"),
            bottom=Side(style="thin", color="CCCCCC")
        )
        for row in ws.iter_rows():
            for cell in row:
                cell.border = border

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename=\"reporte_finanzas.xlsx\"'
        return response

    # --- CONSULTA FINAL ---
    registros = IngresoMensual.objects.all().order_by("id")
    periodos = IngresoMensual.objects.values_list("periodo", flat=True).distinct().order_by("id")

    # --- FILTRO POR PERIODO ---
    inicio = request.GET.get("inicio")
    fin = request.GET.get("fin")
    registros_qs = IngresoMensual.objects.all().order_by("id")

    if inicio and fin:
        try:
            inicio_obj = IngresoMensual.objects.get(periodo=inicio)
            fin_obj = IngresoMensual.objects.get(periodo=fin)
            registros_qs = registros_qs.filter(id__gte=inicio_obj.id, id__lte=fin_obj.id)
        except IngresoMensual.DoesNotExist:
            registros_qs = IngresoMensual.objects.none()  # No existe alguno de los periodos
    elif inicio:  # solo inicio
        try:
            inicio_obj = IngresoMensual.objects.get(periodo=inicio)
            registros_qs = registros_qs.filter(id__gte=inicio_obj.id)
        except IngresoMensual.DoesNotExist:
            registros_qs = IngresoMensual.objects.none()
    elif fin:  # solo fin
        try:
            fin_obj = IngresoMensual.objects.get(periodo=fin)
            registros_qs = registros_qs.filter(id__lte=fin_obj.id)
        except IngresoMensual.DoesNotExist:
            registros_qs = IngresoMensual.objects.none()

    registros = list(registros_qs)

    # --- CÁLCULOS PARA TARJETAS KPI ---
    total_mantenimiento = sum((r.ingresos_mantenimiento or Decimal(0)) for r in registros)
    total_dppp = sum((r.dppp or Decimal(0)) for r in registros)
    total_netos = sum((r.ingresos_netos_mantenimiento or Decimal(0)) for r in registros)
    promedio_diferencia = (
        sum((r.diferencia_ingresos_fac_vs_cobrados or Decimal(0)) for r in registros) / len(registros)
        if registros else 0
)
    
    # Convierte registros en lista de diccionarios para el JS
    registros_serializados = [model_to_dict(r) for r in registros]
    registros_json = json.dumps(registros_serializados, default=str)

    return render(request, "finanzas/index.html", {
        "form": form,
        "mensaje": mensaje,
        "registros": list(IngresoMensual.objects.all().values()),
        "registros_json": registros_json,
        "periodos": periodos,
        "total_mantenimiento": total_mantenimiento,
        "total_dppp": total_dppp,
        "total_netos": total_netos,
        "promedio_diferencia": promedio_diferencia,
    })

def historial_movimientos(request):
    movimientos = MovimientoLog.objects.all().order_by("-fecha")

    if request.method == "POST" and "eliminar_mov" in request.POST:
        mov_id = request.POST.get("id_mov")
        movimiento = get_object_or_404(MovimientoLog, id=mov_id)
        movimiento.delete()
        messages.success(request, "Movimiento eliminado correctamente.")
        return redirect("historial_movimientos")

    return render(request, "finanzas/historial_movimientos.html", {
        "movimientos": movimientos
    })
