from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db import orm
from materials.models import Material
from django.db.models import Q
from models.stock import get_stock_status, stock_gauge
from utils import parse_int


def materials(request: HttpRequest) -> HttpResponse:
    """Список материалов с общим остатком из базы."""
    query = request.GET.get("q", "").strip()
    rows = orm.materials_with_totals()
    if query:
        rows = rows.filter(Q(name__icontains=query) | Q(unit__icontains=query))
    context = {"rows": orm.material_rows(rows), "query": query}
    return render(request, "materials/material_list.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Карточка материала: остатки по складам и операции."""
    material = Material.objects.filter(pk=material_id).first()
    context: dict[str, object] = {
        "material": material,
        "material_id": material_id,
    }
    if material is not None:
        stock_items = orm.material_stock(material_id)
        total = sum(item["quantity"] for item in stock_items)
        context["row"] = {
            "id": material.id, "min_balance": material.min_balance,
            "total": total,
            **stock_gauge(total, material.min_balance),
        }
        context["status"] = get_stock_status(total, material.min_balance)
        context["stock_items"] = stock_items
        context["operations"] = orm.related_operations().filter(
            material_id=material_id,
        ).order_by("performed_at", "id")
    return render(
        request,
        "materials/material_detail.html",
        context,
        status=404 if material is None else 200,
    )


def find_warehouse(request: HttpRequest) -> HttpResponse:
    """Поиск склада, где есть нужное количество материала."""
    material_id = parse_int(request.GET.get("material"))
    quantity = parse_int(request.GET.get("quantity"))
    searched = "material" in request.GET or "quantity" in request.GET
    material = None
    warehouses = []
    if material_id and quantity:
        material = Material.objects.filter(pk=material_id).first()
        if material is not None:
            warehouses = orm.available_warehouses(material_id, quantity)
    context = {
        "materials": Material.objects.values("id", "name", "unit"),
        "material_id": material_id,
        "quantity": quantity,
        "searched": searched,
        "material": material,
        "warehouses": warehouses,
    }
    return render(request, "materials/find_warehouse.html", context)
