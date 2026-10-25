from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.stock import (
    get_stock_level,
    get_total_balance,
    get_warehouse_stock,
)
from models.warehouses import find_warehouse_by_id
from storage import load_data


def warehouses(request: HttpRequest) -> HttpResponse:
    """Список складов."""
    data = load_data()
    context = {
        "rows": [
            {
                "warehouse": warehouse,
                "positions": len(
                    get_warehouse_stock(data["stock"], warehouse)
                ),
            }
            for warehouse in data["warehouses"]
        ],
    }
    return render(request, "warehouses/warehouse_list.html", context)


def warehouse_detail(request: HttpRequest, warehouse_id: int) -> HttpResponse:
    """Что лежит на выбранном складе."""
    data = load_data()
    warehouse = find_warehouse_by_id(data["warehouses"], warehouse_id)
    context: dict[str, object] = {
        "warehouse": warehouse,
        "warehouse_id": warehouse_id,
    }
    if warehouse is not None:
        rows = []
        for item in get_warehouse_stock(data["stock"], warehouse):
            total = get_total_balance(data["stock"], item.material)
            rows.append({
                "item": item,
                "total": total,
                "level": get_stock_level(total, item.material.min_balance),
            })
        context["rows"] = rows
    return render(
        request,
        "warehouses/warehouse_detail.html",
        context,
        status=404 if warehouse is None else 200,
    )
