from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all, fetch_one, with_gauge


def warehouses(request: HttpRequest) -> HttpResponse:
    """Список складов из базы."""
    context = {"rows": fetch_all("warehouses_with_positions")}
    return render(request, "warehouses/warehouse_list.html", context)


def warehouse_detail(request: HttpRequest, warehouse_id: int) -> HttpResponse:
    """Что лежит на выбранном складе."""
    warehouse = fetch_one("warehouse_by_id", [warehouse_id])
    context: dict[str, object] = {
        "warehouse": warehouse,
        "warehouse_id": warehouse_id,
    }
    if warehouse is not None:
        context["rows"] = with_gauge(
            fetch_all("warehouse_stock", [warehouse_id])
        )
    return render(
        request,
        "warehouses/warehouse_detail.html",
        context,
        status=404 if warehouse is None else 200,
    )
