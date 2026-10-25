import sqlite3
from contextlib import closing

import pytest

from db.database import get_connection
from db.import_json import import_all
from db.queries import QUERIES, fetch_all, fetch_one


def test_tables_created(db_path):
    with closing(get_connection(db_path)) as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert tables == {"materials", "warehouses", "stock", "operations"}


def test_foreign_keys_declared(db_path):
    with closing(get_connection(db_path)) as conn:
        targets = {
            row["table"]
            for row in conn.execute("PRAGMA foreign_key_list(operations)")
        }
    assert targets == {"materials", "warehouses"}


def test_foreign_keys_checked(db_path):
    with closing(get_connection(db_path)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO stock VALUES (99, 1, 5)")


def test_import_counts(db_path):
    with closing(get_connection(db_path)) as conn:
        row = conn.execute(
            """
            SELECT (SELECT COUNT(*) FROM materials) AS materials,
                   (SELECT COUNT(*) FROM warehouses) AS warehouses,
                   (SELECT COUNT(*) FROM stock) AS stock,
                   (SELECT COUNT(*) FROM operations) AS operations
            """
        ).fetchone()
    assert dict(row) == {
        "materials": 2, "warehouses": 2, "stock": 3, "operations": 4,
    }


def test_import_can_run_twice(db_path, tmp_path):
    with closing(get_connection(db_path)) as conn:
        counts = import_all(conn, tmp_path)
        conn.commit()
    assert counts["operations"] == 4


def test_empty_location_becomes_null(db_path):
    assert fetch_one("warehouse_by_id", [2])["location"] is None


def test_at_least_ten_queries():
    assert len(QUERIES) >= 10


def test_materials_with_totals(db_path):
    rows = fetch_all("materials_with_totals")
    totals = {row["name"]: row["total"] for row in rows}
    assert totals == {"Бумага А4": 40, "Картридж": 2}


def test_low_stock_uses_having(db_path):
    names = [row["name"] for row in fetch_all("low_stock")]
    assert names == ["Картридж"]


def test_warehouses_with_quantity(db_path):
    rows = fetch_all("warehouses_with_quantity", [1, 10])
    assert [row["name"] for row in rows] == ["Склад №1"]
    assert fetch_all("warehouses_with_quantity", [1, 100]) == []


def test_operations_list_filter(db_path):
    all_rows = fetch_all("operations_list", [None, None])
    receipts = fetch_all("operations_list", ["receipt", "receipt"])
    assert len(all_rows) == 4
    assert {row["operation_type"] for row in receipts} == {"receipt"}


def test_transfer_has_target_name(db_path):
    row = fetch_one("operation_by_id", [4])
    assert row["target_name"] == "Склад №2"


def test_cancelled_not_counted(db_path):
    rows = fetch_all("consumption_by_material", [0])
    consumed = {row["name"]: row["consumed"] for row in rows}
    assert consumed["Бумага А4"] == 0
    assert fetch_one("summary_counts")["operations_count"] == 3


def test_parameter_is_not_part_of_sql(db_path):
    rows = fetch_all("material_by_id", ["1 OR 1=1"])
    assert rows == []
