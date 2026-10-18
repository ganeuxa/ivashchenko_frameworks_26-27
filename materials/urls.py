from django.urls import path

from . import views

urlpatterns = [
    path("", views.materials, name="materials"),
    path(
        "<int:material_id>/", views.material_detail, name="material_detail"
    ),
]
