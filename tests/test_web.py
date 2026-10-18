import pytest
from django.test import Client, override_settings

from models import Material, Receipt, StockItem, Warehouse, WriteOff
from storage import load_data, save_data

VIEW_MODULES = ("homepage", "materials", "warehouses", "operations")


def use_data(monkeypatch, tmp_path, data):
    save_data(data, tmp_path)
    for module in VIEW_MODULES:
        monkeypatch.setattr(
            f"{module}.views.load_data", lambda: load_data(tmp_path)
        )


@pytest.fixture
def client(tmp_path, monkeypatch):
    paper = Material(1, "Бумага А4", "пачка", 10)
    warehouse = Warehouse(1, "Склад №1", "корпус А")
    use_data(monkeypatch, tmp_path, {
        "materials": [paper],
        "warehouses": [warehouse],
        "stock": [StockItem(paper, warehouse, 40)],
        "operations": [
            Receipt(1, paper, warehouse, 40, "2026-09-01 10:00"),
            WriteOff(2, paper, warehouse, 5, "2026-09-02 11:30", True),
        ],
    })
    return Client()


@pytest.mark.parametrize("url, template", [
    ("/", "homepage/index.html"),
    ("/materials/", "materials/material_list.html"),
    ("/materials/1/", "materials/material_detail.html"),
    ("/warehouses/", "warehouses/warehouse_list.html"),
    ("/warehouses/1/", "warehouses/warehouse_detail.html"),
    ("/operations/", "operations/operation_list.html"),
    ("/operations/1/", "operations/operation_detail.html"),
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


def test_material_page_shows_data(client):
    html = client.get("/materials/1/").content.decode()
    assert "Бумага А4" in html
    assert "40 пачка" in html


def test_list_count_and_date_filter(client):
    html = client.get("/operations/").content.decode()
    assert "Всего операций: 2" in html
    assert "02.09.2026 11:30" in html


def test_cancelled_operation_marked(client):
    html = client.get("/operations/2/").content.decode()
    assert "отменена" in html


def test_gauge_shows_fill_and_minimum(client):
    html = client.get("/materials/").content.decode()
    assert "width: 100%" in html
    assert "left: 25%" in html


def test_navigation_marks_current_section(client):
    html = client.get("/materials/").content.decode()
    assert 'href="/materials/"' in html
    assert 'aria-current="page"' in html


def test_navigation_uses_named_urls(client):
    html = client.get("/").content.decode()
    assert 'href="/materials/"' in html
    assert "homepage/css/style.css" in html
    assert "homepage/js/main.js" in html


def test_empty_lists(tmp_path, monkeypatch):
    use_data(monkeypatch, tmp_path, {
        "materials": [], "warehouses": [], "stock": [], "operations": [],
    })
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
