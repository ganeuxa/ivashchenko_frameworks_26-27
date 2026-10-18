from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.materials import find_material_by_id, sort_materials
from models.operations import get_material_operations
from models.stock import get_stock_status, summarize_material
from storage import load_data


def materials(request: HttpRequest) -> HttpResponse:
    """Список материалов."""
    data = load_data()
    context = {
        "rows": [
            summarize_material(data["stock"], material)
            for material in sort_materials(data["materials"])
        ],
    }
    return render(request, "materials/material_list.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Карточка материала: остатки по складам и операции."""
    data = load_data()
    material = find_material_by_id(data["materials"], material_id)
    context = {"material": material, "material_id": material_id}
    if material is not None:
        row = summarize_material(data["stock"], material)
        context["row"] = row
        context["status"] = get_stock_status(
            row["total"], material.min_balance
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
