from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("index", views.index, name="index"),
    path("historial/", views.historial_movimientos, name="historial_movimientos"),
    path('profile/', views.profile, name='profile'),
    # ---- Solo para staff ----
    path("usuarios/", views.admin_users, name="admin_users"),
    path("configuracion/", views.admin_config, name="admin_config"),
    path("logs/", views.admin_logs, name="admin_logs"),
]
