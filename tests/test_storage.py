import json

from models import Material, StockItem, Transfer, Warehouse
from storage import load_data, save_data


def make_data():
    paper = Material(1, "Бумага", "пачка", 10)
    first = Warehouse(1, "Склад №1", "корпус А")
    second = Warehouse(2, "Склад №2", "корпус Б")
    transfer = Transfer(1, paper, first, second, 5, "2026-10-01 10:00")
    return {
        "materials": [paper],
        "warehouses": [first, second],
        "stock": [StockItem(paper, first, 35), StockItem(paper, second, 5)],
        "operations": [transfer],
    }


def test_save_writes_ids_not_objects(tmp_path):
    save_data(make_data(), tmp_path)
    with open(tmp_path / "operations.json", encoding="utf-8") as file:
        record = json.load(file)[0]
    assert record["material_id"] == 1
    assert record["target_warehouse_id"] == 2


def test_load_restores_links(tmp_path):
    save_data(make_data(), tmp_path)
    data = load_data(tmp_path)
    operation = data["operations"][0]
    assert isinstance(operation, Transfer)
    assert operation.material is data["materials"][0]
    assert operation.target_warehouse is data["warehouses"][1]
    assert data["stock"][0].quantity == 35


def test_missing_files_give_empty_data(tmp_path):
    data = load_data(tmp_path)
    assert data["materials"] == []
    assert data["operations"] == []


def test_broken_json(tmp_path):
    (tmp_path / "materials.json").write_text("{не json", encoding="utf-8")
    assert load_data(tmp_path)["materials"] == []


def test_operation_with_unknown_material_skipped(tmp_path):
    save_data(make_data(), tmp_path)
    (tmp_path / "materials.json").write_text("[]", encoding="utf-8")
    data = load_data(tmp_path)
    assert data["operations"] == []
    assert data["stock"] == []
