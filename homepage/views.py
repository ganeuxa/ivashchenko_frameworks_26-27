from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.queries import fetch_all, fetch_one, with_gauge


def index(request: HttpRequest) -> HttpResponse:
    """Главная: что пора дозаказать и короткая сводка из базы."""
    context = {
        "summary": fetch_one("summary_counts"),
        "shortages": with_gauge(fetch_all("low_stock")),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Своя страница 404 для неизвестных адресов."""
    return render(request, "homepage/404.html", status=404)
