from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all, fetch_one, with_dates, with_gauge
from models.stock import get_stock_status, stock_gauge
from utils import parse_int


def materials(request: HttpRequest) -> HttpResponse:
    """Список материалов с общим остатком из базы."""
    context = {"rows": with_gauge(fetch_all("materials_with_totals"))}
    return render(request, "materials/material_list.html", context)


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Карточка материала: остатки по складам и операции."""
    material = fetch_one("material_by_id", [material_id])
    context: dict[str, object] = {
        "material": material,
        "material_id": material_id,
    }
    if material is not None:
        stock_items = fetch_all("material_stock", [material_id])
        total = sum(item["quantity"] for item in stock_items)
        context["row"] = {
            **dict(material),
            "total": total,
            **stock_gauge(total, material["min_balance"]),
        }
        context["status"] = get_stock_status(total, material["min_balance"])
        context["stock_items"] = stock_items
        context["operations"] = with_dates(
            fetch_all("material_operations", [material_id])
        )
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
        material = fetch_one("material_by_id", [material_id])
        if material is not None:
            warehouses = fetch_all(
                "warehouses_with_quantity", [material_id, quantity]
            )
    context = {
        "materials": fetch_all("materials_list"),
        "material_id": material_id,
        "quantity": quantity,
        "searched": searched,
        "material": material,
        "warehouses": warehouses,
    }
    return render(request, "materials/find_warehouse.html", context)
