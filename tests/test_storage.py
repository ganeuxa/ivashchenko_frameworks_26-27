from storage import load_data, save_data


def test_save_and_load(tmp_path):
    data = {
        "materials": {
            1: {"name": "Бумага", "unit": "пачка", "min_balance": 10},
        },
        "warehouses": {1: {"name": "Склад №1", "location": "корпус А"}},
        "stock": {(1, 1): 40},
        "operations": [],
    }
    save_data(data, tmp_path)
    assert load_data(tmp_path) == data


def test_missing_files_give_empty_data(tmp_path):
    data = load_data(tmp_path)
    assert data["materials"] == {}
    assert data["stock"] == {}


def test_broken_json(tmp_path):
    (tmp_path / "materials.json").write_text("{не json", encoding="utf-8")
    assert load_data(tmp_path)["materials"] == {}
