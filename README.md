# Control‑Financiero — Documentación técnica (completa)

## 1. Resumen del proyecto
**Control‑Financiero** es una aplicación web desarrollada con **Django (v4.2.7)**. La app principal se llama `dashboard` y permite:
- Registrar ingresos por periodo y por partidas contables.
- Añadir movimientos y llevar un historial (auditoría).
- Exportar reportes a Excel.
- Gestionar usuarios y revisar logs (vistas de administración).

El proyecto incluye una base de datos SQLite (`db.sqlite3`) y dependencias descritas en `requirements.txt`.


## 2. Estructura del proyecto
Raíz principal (resumida):

```
Control-Financiero-main/
├─ control_financiero/         # proyecto Django (settings, urls)
├─ dashboard/                  # aplicación principal (modelos, vistas, forms, templates)
│  ├─ migrations/
│  ├─ templates/finanzas/
│  ├─ models.py
│  ├─ views.py
│  ├─ urls.py
│  ├─ forms.py
│  └─ admin.py
├─ db.sqlite3
├─ manage.py
└─ requirements.txt
```


## 3. Modelos de datos (resumen)
Se detectaron tres modelos principales en `dashboard/models.py`:

### IngresoMensual
Modelo que agrupa montos por `periodo` (ej. "Jan-25") y muchas columnas decimal para partidas contables:
- `periodo` — CharField(max_length=10)
- `ingresos_mantenimiento`, `dppp`, `ingresos_netos_mantenimiento`, ..., `observaciones` — Decimal/TextFields

Uso: consolidado mensual por partidas; se utiliza para mostrar dashboards y exportar reportes.

### MovimientoLog
Registro de movimientos/ajustes realizados por usuarios:
- `fecha` — DateTimeField(default=timezone.now)
- `tipo` — CharField(max_length=20)
- `periodo`, `columna`, `monto`, `observaciones`

Uso: historial detallado de cambios que afectaron `IngresoMensual`.

### SystemLog
Auditoría general:
- `fecha`, `usuario` (ForeignKey a auth.User), `accion`, `detalle`

Uso: histórico de acciones del sistema (vistas administrativas).


## 4. Vistas y endpoints principales
Definidas en `dashboard/urls.py` y `dashboard/views.py`:

- `/` → `login_view` (GET: mostrar login, POST: autenticar)
- `/logout/` → `logout_view`
- `/index` → `index` (dashboard principal: ver periodos, añadir movimiento, exportar Excel)
- `/historial/` → `historial_movimientos` (consultar `MovimientoLog`)
- `/profile/` → `profile` (editar email / perfil)
- `/usuarios/`, `/configuracion/`, `/logs/` → vistas accesibles solo para staff (`@user_passes_test(lambda u: u.is_staff)`)

Operaciones notables:
- Export a Excel: la vista genera un `Workbook` (openpyxl) con los datos y lo devuelve como attachment.
- Añadir movimiento: `MovimientoForm` POST crea `MovimientoLog` y actualiza `IngresoMensual` (según la columna).


## 5. Formularios (resumen)
Principales formularios en `dashboard/forms.py`:

- `MovimientoForm`: formulario para seleccionar/crear periodo, elegir columna y monto, agregar observaciones.
- `ProfileUpdateForm`: actualizar email del usuario.
- `CustomLoginForm`, `CustomUserCreationForm` (adaptaciones de formularios de autenticación).

Notas: `MovimientoForm` usa `ModelChoiceField` sobre `IngresoMensual` para seleccionar periodos existentes.


## 6. Dependencias y configuración
Dependencias en `requirements.txt` incluyen (entre otras):
- Django==4.2.7
- pandas==2.1.3
- openpyxl==3.1.2
- python-decouple, whitenoise, gunicorn, psycopg2-binary, celery, redis, django-crispy-forms, crispy-bootstrap5, django-debug-toolbar

`settings.py` usa SQLite por defecto:
```
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': BASE_DIR / 'db.sqlite3',
  }
}
```

Recomendaciones para producción:
- `DEBUG=False`, configurar `ALLOWED_HOSTS`.
- Usar PostgreSQL para producción y configurar `STATIC_ROOT`.
- Configurar variables sensibles en `.env` con `python-decouple`.
