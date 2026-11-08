from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db import orm


def index(request: HttpRequest) -> HttpResponse:
    """Главная: что пора дозаказать и короткая сводка из базы."""
    context = {
        "summary": orm.summary(),
        "shortages": orm.shortages(),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Своя страница 404 для неизвестных адресов."""
    return render(request, "homepage/404.html", status=404)
