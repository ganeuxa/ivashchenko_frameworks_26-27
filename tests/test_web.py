from contextlib import closing

import pytest
from django.test import Client, override_settings

from db.database import create_schema, get_connection


@pytest.fixture
def client(db_path):
    return Client()


@pytest.mark.parametrize("url, template", [
    ("/", "homepage/index.html"),
    ("/materials/", "materials/material_list.html"),
    ("/materials/1/", "materials/material_detail.html"),
    ("/materials/find/", "materials/find_warehouse.html"),
    ("/warehouses/", "warehouses/warehouse_list.html"),
    ("/warehouses/1/", "warehouses/warehouse_detail.html"),
    ("/operations/", "operations/operation_list.html"),
    ("/operations/1/", "operations/operation_detail.html"),
    ("/operations/statistics/", "operations/statistics.html"),
])
def test_pages_use_templates(client, url, template):
    response = client.get(url)
    assert response.status_code == 200
    names = [used.name for used in response.templates]
    assert template in names
    assert "base.html" in names


@pytest.mark.parametrize("url", [
    "/materials/999/",
    "/warehouses/999/",
    "/operations/999/",
])
def test_unknown_id_gives_404(client, url):
    response = client.get(url)
    assert response.status_code == 404
    assert "не найден" in response.content.decode()


def test_material_page_shows_data_from_db(client):
    html = client.get("/materials/1/").content.decode()
    assert "Бумага А4" in html
    assert "35 пачка" in html


def test_home_shows_low_stock(client):
    html = client.get("/").content.decode()
    assert "Картридж" in html
    assert "проведённых операций: 3" in html


def test_operations_filter_by_type(client):
    html = client.get("/operations/?type=receipt").content.decode()
    assert "Показано операций: 2" in html
    assert "Перемещение" not in html.split("<tbody>")[1]


def test_unknown_type_shows_all(client):
    html = client.get("/operations/?type=hack").content.decode()
    assert "Показано операций: 4" in html


def test_list_date_filter(client):
    html = client.get("/operations/").content.decode()
    assert "02.09.2026 11:30" in html


def test_cancelled_operation_marked(client):
    html = client.get("/operations/2/").content.decode()
    assert "отменена" in html


def test_transfer_shows_both_warehouses(client):
    html = client.get("/operations/4/").content.decode()
    assert "Откуда" in html
    assert "Склад №2" in html


def test_find_warehouse(client):
    html = client.get("/materials/find/?material=1&quantity=10").content
    assert "Склад №1" in html.decode()
    html = client.get("/materials/find/?material=1&quantity=500").content
    assert "Ни на одном складе столько нет" in html.decode()


def test_find_warehouse_bad_input(client):
    response = client.get("/materials/find/?material=abc&quantity=-5")
    assert response.status_code == 200
    assert "целым числом" in response.content.decode()


def test_statistics_threshold(client):
    html = client.get("/operations/statistics/?min=1").content.decode()
    assert "Таких материалов нет" in html


def test_gauge_shows_fill_and_minimum(client):
    html = client.get("/materials/").content.decode()
    assert "width: 100%" in html
    assert "left: 25%" in html


def test_navigation_marks_current_section(client):
    html = client.get("/operations/statistics/").content.decode()
    assert html.count('aria-current="page"') == 1


def test_navigation_uses_named_urls(client):
    html = client.get("/").content.decode()
    assert 'href="/materials/"' in html
    assert 'href="/operations/statistics/"' in html
    assert "homepage/css/style.css" in html
    assert "homepage/js/main.js" in html


def test_empty_database(tmp_path, monkeypatch):
    path = tmp_path / "empty.sqlite"
    with closing(get_connection(path)) as conn:
        create_schema(conn)
    monkeypatch.setattr("db.database.DB_PATH", path)
    client = Client()
    assert "Материалов пока нет" in client.get("/materials/").content.decode()
    assert "Операций пока нет" in client.get("/operations/").content.decode()


def test_material_id_must_be_number(client):
    assert client.get("/materials/abc/").status_code == 404


@override_settings(DEBUG=False)
def test_custom_404_page(client):
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "Страница не найдена" in response.content.decode()
