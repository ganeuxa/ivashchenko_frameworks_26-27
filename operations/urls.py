from django.urls import path

from . import views

urlpatterns = [
    path("", views.operations, name="operations"),
    path(
        "<int:operation_id>/",
        views.operation_detail,
        name="operation_detail",
    ),
]
