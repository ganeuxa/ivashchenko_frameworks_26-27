from datetime import date

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from db import orm
from operations.models import Operation
from utils import parse_int

OPERATION_TITLES = dict(Operation.Type.choices)
SORTS = {
    "newest": ("-performed_at", "-id"),
    "oldest": ("performed_at", "id"),
    "material": ("material__name", "-performed_at", "-id"),
    "quantity": ("-quantity", "-id"),
}


def operations(request):
    operation_type = request.GET.get("type")
    if operation_type not in OPERATION_TITLES:
        operation_type = None
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest")
    if sort not in SORTS:
        sort = "newest"
    rows = orm.related_operations()
    if operation_type:
        rows = rows.filter(type=operation_type)
    if query:
        rows = rows.filter(
            Q(material__name__icontains=query)
            | Q(warehouse__name__icontains=query)
            | Q(target_warehouse__name__icontains=query)
        )
    hide_cancelled = request.GET.get("hide_cancelled") == "1"
    if hide_cancelled:
        rows = rows.exclude(is_cancelled=True)
    warehouse_id = parse_int(request.GET.get("warehouse"))
    if warehouse_id:
        rows = rows.filter(Q(warehouse_id=warehouse_id)
                           | Q(target_warehouse_id=warehouse_id))
    errors = []
    dates = {}
    for param, lookup in (("from", "gte"), ("to", "lte")):
        value = request.GET.get(param, "")
        dates[param] = value
        if value:
            try:
                parsed = date.fromisoformat(value)
            except ValueError:
                errors.append("Дата должна быть в формате ГГГГ-ММ-ДД.")
            else:
                rows = rows.filter(**{f"performed_at__date__{lookup}": parsed})
    page = Paginator(rows.order_by(*SORTS[sort]), 10).get_page(
        request.GET.get("page"),
    )
    return render(request, "operations/operation_list.html", {
        "operations": page.object_list, "page_obj": page,
        "titles": OPERATION_TITLES, "current_type": operation_type,
        "query": query, "sort": sort, "hide_cancelled": hide_cancelled,
        "warehouse_id": warehouse_id, "warehouses": orm.warehouse_positions(),
        "date_from": dates["from"], "date_to": dates["to"], "errors": errors,
    })


def operation_detail(request, operation_id):
    operation = orm.related_operations().filter(pk=operation_id).first()
    return render(request, "operations/operation_detail.html", {
        "operation": operation, "operation_id": operation_id,
    }, status=404 if operation is None else 200)


def statistics(request):
    minimum = parse_int(request.GET.get("min"), min_value=0) or 0
    return render(request, "operations/statistics.html",
                  orm.statistics_data(minimum))
