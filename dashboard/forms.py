from django import forms
from .models import IngresoMensual
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

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

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Correo electrónico")
    is_staff = forms.BooleanField(required=False, label="Es administrador?")

    class Meta:
        model = User
        fields = ("username", "email", "is_staff", "password1", "password2")

# --- FORMULARIO DE LOGIN ---
class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

# --- FORMULARIO DE PERFIL (actualización de correo) ---
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

