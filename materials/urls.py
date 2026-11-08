from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("", views.materials, name="list"),
    path("find/", views.find_warehouse, name="find"),
    path("<int:material_id>/", views.material_detail, name="detail"),
    path("<slug:slug>/", views.material_by_slug, name="by_slug"),
]
