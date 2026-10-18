from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models import Material, StockItem
from models.materials import find_material_by_id, sort_materials
from models.operations import get_material_operations
from models.stock import get_stock_level, get_stock_status, get_total_balance
from storage import load_data


def material_summary(stock: list[StockItem], material: Material) -> dict:
    """Материал вместе с общим остатком и уровнем для шаблона."""
    total = get_total_balance(stock, material)
    return {
        "material": material,
        "total": total,
        "level": get_stock_level(total, material.min_balance),
    }


def materials(request: HttpRequest) -> HttpResponse:
    """Список материалов."""
    data = load_data()
    context = {
        "rows": [
            material_summary(data["stock"], material)
            for material in sort_materials(data["materials"])
        ],
    }
    return render(request, "materials/material_list.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Карточка материала: остатки по складам и операции."""
    data = load_data()
    material = find_material_by_id(data["materials"], material_id)
    context = {"material": material}
    if material is not None:
        summary = material_summary(data["stock"], material)
        context.update(summary)
        context["status"] = get_stock_status(
            summary["total"], material.min_balance
        )
        context["stock_items"] = [
            item for item in data["stock"]
            if item.material is material and item.quantity > 0
        ]
        context["operations"] = get_material_operations(
            data["operations"], material
        )
    return render(
        request,
        "materials/material_detail.html",
        context,
        status=404 if material is None else 200,
    )
