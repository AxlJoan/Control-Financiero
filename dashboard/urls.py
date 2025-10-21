from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("historial/", views.historial_movimientos, name="historial_movimientos"),
]
