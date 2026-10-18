from django.urls import path

from . import views

urlpatterns = [
    path("", views.warehouses, name="warehouses"),
    path(
        "<int:warehouse_id>/",
        views.warehouse_detail,
        name="warehouse_detail",
    ),
]
