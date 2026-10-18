import pytest
from django.test import Client, override_settings

from models import Material, Receipt, StockItem, Warehouse
from storage import load_data, save_data


@pytest.fixture
def client(tmp_path, monkeypatch):
    paper = Material(1, "Бумага А4", "пачка", 10)
    warehouse = Warehouse(1, "Склад №1", "корпус А")
    save_data(
        {
            "materials": [paper],
            "warehouses": [warehouse],
            "stock": [StockItem(paper, warehouse, 40)],
            "operations": [
                Receipt(1, paper, warehouse, 40, "2026-09-01 10:00")
            ],
        },
        tmp_path,
    )
    for module in ("homepage", "materials", "warehouses", "operations"):
        monkeypatch.setattr(
            f"{module}.views.load_data", lambda: load_data(tmp_path)
        )
    return Client()


@pytest.mark.parametrize("url", [
    "/",
    "/materials/",
    "/materials/1/",
    "/warehouses/",
    "/warehouses/1/",
    "/operations/",
    "/operations/1/",
])
def test_pages_open(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", [
    "/materials/999/",
    "/warehouses/999/",
    "/operations/999/",
])
def test_unknown_id_gives_404(client, url):
    assert client.get(url).status_code == 404


def test_material_page_shows_data(client):
    html = client.get("/materials/1/").content.decode()
    assert "Бумага А4" in html
    assert "40 пачка" in html


def test_material_id_must_be_number(client):
    assert client.get("/materials/abc/").status_code == 404


@override_settings(DEBUG=False)
def test_custom_404_page(client):
    response = client.get("/nonexistent/")
    assert response.status_code == 404
    assert "страница не найдена" in response.content.decode()
