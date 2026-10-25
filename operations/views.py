from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all, fetch_one, with_dates
from models.operations import OPERATION_CLASSES
from utils import parse_int

OPERATION_TITLES = {
    operation_type: operation_class.title
    for operation_type, operation_class in OPERATION_CLASSES.items()
}


def operations(request: HttpRequest) -> HttpResponse:
    """История операций из базы, можно отобрать один тип."""
    operation_type = request.GET.get("type")
    if operation_type not in OPERATION_TITLES:
        operation_type = None
    context = {
        "operations": with_dates(
            fetch_all("operations_list", [operation_type, operation_type])
        ),
        "titles": OPERATION_TITLES,
        "current_type": operation_type,
    }
    return render(request, "operations/operation_list.html", context)


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Карточка одной операции."""
    row = fetch_one("operation_by_id", [operation_id])
    operation = with_dates([row])[0] if row is not None else None
    return render(
        request,
        "operations/operation_detail.html",
        {"operation": operation, "operation_id": operation_id},
        status=404 if operation is None else 200,
    )


def statistics(request: HttpRequest) -> HttpResponse:
    """Статистика: операции по типам и складам, расход материалов."""
    min_consumed = parse_int(request.GET.get("min"), min_value=0) or 0
    context = {
        "by_type": with_dates(
            fetch_all("operations_by_type"), ("first_at", "last_at")
        ),
        "by_warehouse": fetch_all("operations_by_warehouse"),
        "consumption": fetch_all("consumption_by_material", [min_consumed]),
        "min_consumed": min_consumed,
    }
    return render(request, "operations/statistics.html", context)
