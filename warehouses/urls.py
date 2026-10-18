from django.urls import path

from . import views

app_name = "warehouses"

urlpatterns = [
    path("", views.warehouses, name="list"),
    path("<int:warehouse_id>/", views.warehouse_detail, name="detail"),
]
