from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db import orm
from warehouses.models import Warehouse


def warehouses(request: HttpRequest) -> HttpResponse:
    """Список складов из базы."""
    context = {"rows": orm.warehouse_positions()}
    return render(request, "warehouses/warehouse_list.html", context)


def warehouse_detail(request: HttpRequest, warehouse_id: int) -> HttpResponse:
    """Что лежит на выбранном складе."""
    warehouse = Warehouse.objects.filter(pk=warehouse_id).first()
    context: dict[str, object] = {
        "warehouse": warehouse,
        "warehouse_id": warehouse_id,
    }
    if warehouse is not None:
        context["rows"] = orm.warehouse_stock(warehouse_id)
    return render(
        request,
        "warehouses/warehouse_detail.html",
        context,
        status=404 if warehouse is None else 200,
    )
