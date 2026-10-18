from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

from homepage.views import not_found_page, page, status_badge
from models.stock import get_total_balance, get_warehouse_stock
from models.warehouses import find_warehouse_by_id
from storage import load_data


def warehouses(request: HttpRequest) -> HttpResponse:
    """Список складов."""
    data = load_data()
    items = ""
    for warehouse in data["warehouses"]:
        positions = len(get_warehouse_stock(data["stock"], warehouse))
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <div>
                <a href="/warehouses/{warehouse.id}/">
                    {escape(warehouse.name)}
                </a>
                <div class="text-muted small">
                    {escape(warehouse.location)}
                </div>
            </div>
            <span class="badge bg-primary align-self-center">
                позиций: {positions}
            </span>
        </li>
        """
    content = f"""
    <h1>Склады</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Склады", content))


def warehouse_detail(request: HttpRequest, warehouse_id: int) -> HttpResponse:
    """Что лежит на выбранном складе."""
    data = load_data()
    warehouse = find_warehouse_by_id(data["warehouses"], warehouse_id)
    if warehouse is None:
        return not_found_page(
            "Склад не найден", "/warehouses/", "← к списку складов"
        )

    rows = ""
    for item in get_warehouse_stock(data["stock"], warehouse):
        material = item.material
        total = get_total_balance(data["stock"], material)
        rows += f"""
        <tr>
            <td>
                <a href="/materials/{material.id}/">
                    {escape(material.name)}
                </a>
            </td>
            <td>{item.quantity} {escape(material.unit)}</td>
            <td>{status_badge(total, material.min_balance)}</td>
        </tr>
        """
    if not rows:
        rows = '<tr><td colspan="3">Склад пустой</td></tr>'

    content = f"""
    <h1>{escape(warehouse.name)}</h1>
    <p class="text-muted">{escape(warehouse.location)}</p>
    <table class="table bg-white">
        <thead>
            <tr><th>Материал</th><th>На складе</th><th>Общий статус</th></tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <a href="/warehouses/" class="btn btn-outline-secondary">
        ← к списку складов
    </a>
    """
    return HttpResponse(page(escape(warehouse.name), content))
