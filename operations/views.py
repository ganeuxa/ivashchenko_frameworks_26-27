from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

from homepage.views import not_found_page, page
from models import Operation
from models.operations import find_operation_by_id
from storage import load_data


def operation_badge(operation: Operation) -> str:
    """Бейдж: проведена операция или отменена."""
    if operation.is_cancelled:
        return '<span class="badge bg-secondary">отменена</span>'
    return '<span class="badge bg-success">проведена</span>'


def operations(request: HttpRequest) -> HttpResponse:
    """История операций, новые сверху."""
    data = load_data()
    rows = ""
    for operation in reversed(data["operations"]):
        rows += f"""
        <tr>
            <td>
                <a href="/operations/{operation.id}/">{operation.id}</a>
            </td>
            <td>{escape(operation.date)}</td>
            <td>{operation.title}</td>
            <td>{escape(operation.material.name)}</td>
            <td>{operation.quantity} {escape(operation.material.unit)}</td>
            <td>{escape(operation.place())}</td>
            <td>{operation_badge(operation)}</td>
        </tr>
        """
    content = f"""
    <h1>Операции</h1>
    <table class="table table-hover bg-white">
        <thead>
            <tr>
                <th>№</th><th>Дата</th><th>Тип</th><th>Материал</th>
                <th>Количество</th><th>Склад</th><th>Статус</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """
    return HttpResponse(page("Операции", content))


def operation_detail(request: HttpRequest, operation_id: int) -> HttpResponse:
    """Карточка одной операции."""
    data = load_data()
    operation = find_operation_by_id(data["operations"], operation_id)
    if operation is None:
        return not_found_page(
            "Операция не найдена", "/operations/", "← к истории операций"
        )

    material = operation.material
    content = f"""
    <div class="card">
        <div class="card-body">
            <h1 class="card-title h3">
                {operation.title} №{operation.id}
                {operation_badge(operation)}
            </h1>
            <p class="card-text">Дата: {escape(operation.date)}</p>
            <p class="card-text">
                Материал:
                <a href="/materials/{material.id}/">
                    {escape(material.name)}
                </a>
            </p>
            <p class="card-text">
                Количество: {operation.quantity} {escape(material.unit)}
            </p>
            <p class="card-text">Склад: {escape(operation.place())}</p>
            <a href="/operations/" class="btn btn-outline-secondary">
                ← к истории операций
            </a>
        </div>
    </div>
    """
    return HttpResponse(
        page(f"{operation.title} №{operation.id}", content)
    )
