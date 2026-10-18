from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.operations import find_operation_by_id
from storage import load_data


def operations(request: HttpRequest) -> HttpResponse:
    """История операций, новые сверху."""
    data = load_data()
    context = {
        "operations": list(reversed(data["operations"])),
    }
    return render(request, "operations/operation_list.html", context)


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Карточка одной операции."""
    data = load_data()
    operation = find_operation_by_id(data["operations"], operation_id)
    return render(
        request,
        "operations/operation_detail.html",
        {"operation": operation, "operation_id": operation_id},
        status=404 if operation is None else 200,
    )
