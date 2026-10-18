from django.urls import path

from . import views

app_name = "materials"

urlpatterns = [
    path("", views.materials, name="list"),
    path("<int:material_id>/", views.material_detail, name="detail"),
]
