from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.stock import low_stock_materials
from storage import load_data


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница."""
    data = load_data()
    context = {
        "materials_count": len(data["materials"]),
        "warehouses_count": len(data["warehouses"]),
        "operations_count": len(data["operations"]),
        "low_stock": list(
            low_stock_materials(data["materials"], data["stock"])
        ),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Своя страница 404 для неизвестных адресов."""
    return render(request, "homepage/404.html", status=404)
