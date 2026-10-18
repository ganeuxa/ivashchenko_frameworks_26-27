from django.http import HttpRequest, HttpResponse

from models.stock import get_total_balance, low_stock_materials
from storage import load_data

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
)


def page(title: str, content: str) -> str:
    """Общий каркас HTML-страницы: Bootstrap, меню и содержимое."""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_CSS}">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">Учёт материалов</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/materials/">Материалы</a>
                <a class="nav-link" href="/warehouses/">Склады</a>
                <a class="nav-link" href="/operations/">Операции</a>
            </div>
        </div>
    </nav>
    <main class="container pb-5">{content}</main>
</body>
</html>"""


def status_badge(total: int, minimum: int) -> str:
    """Цветной бейдж со статусом остатка."""
    if total == 0:
        return '<span class="badge bg-danger">закончился</span>'
    elif total < minimum:
        return '<span class="badge bg-warning text-dark">ниже минимума</span>'
    return '<span class="badge bg-success">в норме</span>'


def not_found_page(title: str, back_url: str, back_text: str) -> HttpResponse:
    """Страница «не найдено» с кодом 404."""
    content = f"""
    <h1 class="text-danger">{title}</h1>
    <a href="{back_url}" class="btn btn-outline-secondary">{back_text}</a>
    """
    return HttpResponse(page(title, content), status=404)


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница."""
    data = load_data()
    low_count = len(
        list(low_stock_materials(data["materials"], data["stock"]))
    )
    total_units = sum(
        get_total_balance(data["stock"], material)
        for material in data["materials"]
    )
    content = f"""
    <h1 class="display-5">Учёт расходных материалов</h1>
    <p class="lead">
        Что лежит на складах, сколько осталось и что пора дозаказать.
    </p>
    <div class="row g-3 my-3">
        <div class="col-6 col-md-3">
            <div class="card text-center"><div class="card-body">
                <div class="fs-2">{len(data["materials"])}</div>
                <div class="text-muted">материалов</div>
            </div></div>
        </div>
        <div class="col-6 col-md-3">
            <div class="card text-center"><div class="card-body">
                <div class="fs-2">{len(data["warehouses"])}</div>
                <div class="text-muted">складов</div>
            </div></div>
        </div>
        <div class="col-6 col-md-3">
            <div class="card text-center"><div class="card-body">
                <div class="fs-2">{total_units}</div>
                <div class="text-muted">единиц на складах</div>
            </div></div>
        </div>
        <div class="col-6 col-md-3">
            <div class="card text-center border-warning">
            <div class="card-body">
                <div class="fs-2">{low_count}</div>
                <div class="text-muted">пора дозаказать</div>
            </div></div>
        </div>
    </div>
    <a href="/materials/" class="btn btn-primary me-2">Материалы</a>
    <a href="/warehouses/" class="btn btn-secondary me-2">Склады</a>
    <a href="/operations/" class="btn btn-outline-secondary">Операции</a>
    """
    return HttpResponse(page("Учёт расходных материалов", content))


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Своя страница 404 для неизвестных адресов."""
    return not_found_page(
        "404: страница не найдена", "/", "На главную"
    )
