from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

from homepage.views import not_found_page, page, status_badge
from models.materials import find_material_by_id, sort_materials
from models.operations import get_material_operations
from models.stock import get_stock_status, get_total_balance
from storage import load_data


def materials(request: HttpRequest) -> HttpResponse:
    """Список материалов с общим остатком и статусом."""
    data = load_data()
    rows = ""
    for material in sort_materials(data["materials"]):
        total = get_total_balance(data["stock"], material)
        rows += f"""
        <tr>
            <td>{material.id}</td>
            <td>
                <a href="/materials/{material.id}/">
                    {escape(material.name)}
                </a>
            </td>
            <td>{total} {escape(material.unit)}</td>
            <td>{material.min_balance}</td>
            <td>{status_badge(total, material.min_balance)}</td>
        </tr>
        """
    content = f"""
    <h1>Материалы</h1>
    <table class="table table-hover bg-white">
        <thead>
            <tr>
                <th>№</th><th>Название</th><th>Остаток</th>
                <th>Минимум</th><th>Статус</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """
    return HttpResponse(page("Материалы", content))


def material_detail(request: HttpRequest, material_id: int) -> HttpResponse:
    """Карточка материала: остатки по складам и операции."""
    data = load_data()
    material = find_material_by_id(data["materials"], material_id)
    if material is None:
        return not_found_page(
            "Материал не найден", "/materials/", "← к списку материалов"
        )

    unit = escape(material.unit)
    total = get_total_balance(data["stock"], material)
    stock_rows = ""
    for item in data["stock"]:
        if item.material is material and item.quantity > 0:
            stock_rows += f"""
            <li class="list-group-item d-flex justify-content-between">
                <a href="/warehouses/{item.warehouse.id}/">
                    {escape(item.warehouse.name)}
                </a>
                <span>{item.quantity} {unit}</span>
            </li>
            """
    if not stock_rows:
        stock_rows = '<li class="list-group-item">Нигде нет</li>'

    operation_rows = ""
    for operation in get_material_operations(data["operations"], material):
        operation_rows += f"""
        <li class="list-group-item">
            <a href="/operations/{operation.id}/">
                {escape(str(operation))}
            </a>
        </li>
        """
    if not operation_rows:
        operation_rows = '<li class="list-group-item">Операций нет</li>'

    content = f"""
    <div class="card mb-4">
        <div class="card-body">
            <h1 class="card-title h3">{escape(material.name)}</h1>
            <p class="card-text">Номер: {material.id}</p>
            <p class="card-text">Единица измерения: {unit}</p>
            <p class="card-text">
                Минимальный остаток: {material.min_balance} {unit}
            </p>
            <p class="card-text">
                Всего на складах: <strong>{total} {unit}</strong>
                {status_badge(total, material.min_balance)}
            </p>
            <p class="card-text text-muted">
                {get_stock_status(total, material.min_balance)}
            </p>
        </div>
    </div>
    <h2 class="h5">По складам</h2>
    <ul class="list-group mb-4">{stock_rows}</ul>
    <h2 class="h5">Операции</h2>
    <ul class="list-group mb-4">{operation_rows}</ul>
    <a href="/materials/" class="btn btn-outline-secondary">
        ← к списку материалов
    </a>
    """
    return HttpResponse(page(escape(material.name), content))
