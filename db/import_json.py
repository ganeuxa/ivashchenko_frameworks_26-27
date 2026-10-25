import sqlite3
from contextlib import closing
from pathlib import Path

from db.database import create_schema, get_connection
from storage import (
    DATA_DIR,
    MATERIAL_FIELDS,
    OPERATION_FIELDS,
    STOCK_FIELDS,
    WAREHOUSE_FIELDS,
    read_json,
)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Очищает таблицы, сначала те, что ссылаются на другие."""
    conn.execute("DELETE FROM operations")
    conn.execute("DELETE FROM stock")
    conn.execute("DELETE FROM materials")
    conn.execute("DELETE FROM warehouses")


def import_warehouses(conn: sqlite3.Connection, data_dir: Path) -> int:
    """Переносит склады из warehouses.json."""
    records = read_json(data_dir / "warehouses.json", WAREHOUSE_FIELDS)
    conn.executemany(
        "INSERT INTO warehouses (id, name, location) VALUES (?, ?, ?)",
        [
            (record["id"], record["name"], record["location"] or None)
            for record in records
        ],
    )
    return len(records)


def import_materials(conn: sqlite3.Connection, data_dir: Path) -> int:
    """Переносит материалы из materials.json."""
    records = read_json(data_dir / "materials.json", MATERIAL_FIELDS)
    conn.executemany(
        """
        INSERT INTO materials (id, name, unit, min_balance)
        VALUES (?, ?, ?, ?)
        """,
        [
            (record["id"], record["name"], record["unit"],
             record["min_balance"])
            for record in records
        ],
    )
    return len(records)


def import_stock(conn: sqlite3.Connection, data_dir: Path) -> int:
    """Переносит остатки из stock.json."""
    records = read_json(data_dir / "stock.json", STOCK_FIELDS)
    conn.executemany(
        """
        INSERT INTO stock (material_id, warehouse_id, quantity)
        VALUES (?, ?, ?)
        """,
        [
            (record["material_id"], record["warehouse_id"],
             record["quantity"])
            for record in records
        ],
    )
    return len(records)


def import_operations(conn: sqlite3.Connection, data_dir: Path) -> int:
    """Переносит историю операций из operations.json."""
    records = read_json(data_dir / "operations.json", OPERATION_FIELDS)
    conn.executemany(
        """
        INSERT INTO operations (
            id, type, material_id, warehouse_id, target_warehouse_id,
            quantity, performed_at, is_cancelled
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                record["id"],
                record["type"],
                record["material_id"],
                record["warehouse_id"],
                record.get("target_warehouse_id"),
                record["quantity"],
                record["date"],
                int(record.get("is_cancelled", False)),
            )
            for record in records
        ],
    )
    return len(records)


def import_all(
    conn: sqlite3.Connection,
    data_dir: Path = DATA_DIR,
) -> dict[str, int]:
    """Создаёт таблицы и заново заполняет их данными из JSON."""
    create_schema(conn)
    clear_tables(conn)
    return {
        "warehouses": import_warehouses(conn, data_dir),
        "materials": import_materials(conn, data_dir),
        "stock": import_stock(conn, data_dir),
        "operations": import_operations(conn, data_dir),
    }


def main() -> None:
    """Переносит данные из data/*.json в базу SQLite."""
    with closing(get_connection()) as conn:
        try:
            counts = import_all(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
