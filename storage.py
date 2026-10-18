import json
from pathlib import Path

from stock import Stock

DATA_DIR = Path(__file__).parent / "data"

MATERIAL_FIELDS = {"id", "name", "unit", "min_balance"}
WAREHOUSE_FIELDS = {"id", "name", "location"}
STOCK_FIELDS = {"material_id", "warehouse_id", "quantity"}
OPERATION_FIELDS = {"id", "type", "material_id", "warehouse_id", "quantity"}


def read_json(path: Path, required_fields: set[str]) -> list[dict]:
    """Читает список записей из JSON, пропуская неполные."""
    try:
        with open(path, encoding="utf-8") as file:
            records = json.load(file)
    except FileNotFoundError:
        print(f"Файл {path.name} не найден, начинаем с пустых данных")
        return []
    except json.JSONDecodeError:
        print(f"Файл {path.name} повреждён, данные из него не загружены")
        return []
    if not isinstance(records, list):
        print(f"В файле {path.name} ожидался список записей")
        return []
    valid_records = [
        record
        for record in records
        if isinstance(record, dict) and required_fields <= record.keys()
    ]
    skipped = len(records) - len(valid_records)
    if skipped:
        print(f"В файле {path.name} пропущено неполных записей: {skipped}")
    return valid_records


def write_json(path: Path, records: list[dict]) -> None:
    """Записывает список записей в JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=4)


def load_materials(path: Path) -> dict[int, dict]:
    """Загружает материалы."""
    return {
        record["id"]: {
            "name": record["name"],
            "unit": record["unit"],
            "min_balance": record["min_balance"],
        }
        for record in read_json(path, MATERIAL_FIELDS)
    }


def save_materials(path: Path, materials: dict[int, dict]) -> None:
    """Сохраняет материалы."""
    write_json(path, [
        {"id": material_id, **material}
        for material_id, material in materials.items()
    ])


def load_warehouses(path: Path) -> dict[int, dict]:
    """Загружает склады."""
    return {
        record["id"]: {"name": record["name"], "location": record["location"]}
        for record in read_json(path, WAREHOUSE_FIELDS)
    }


def save_warehouses(path: Path, warehouses: dict[int, dict]) -> None:
    """Сохраняет склады."""
    write_json(path, [
        {"id": warehouse_id, **warehouse}
        for warehouse_id, warehouse in warehouses.items()
    ])


def load_stock(path: Path) -> Stock:
    """Загружает остатки."""
    return {
        (record["material_id"], record["warehouse_id"]): record["quantity"]
        for record in read_json(path, STOCK_FIELDS)
    }


def save_stock(path: Path, stock: Stock) -> None:
    """Сохраняет остатки."""
    write_json(path, [
        {
            "material_id": material_id,
            "warehouse_id": warehouse_id,
            "quantity": quantity,
        }
        for (material_id, warehouse_id), quantity in stock.items()
    ])


def load_data(data_dir: Path = DATA_DIR) -> dict:
    """Загружает все данные программы."""
    return {
        "materials": load_materials(data_dir / "materials.json"),
        "warehouses": load_warehouses(data_dir / "warehouses.json"),
        "stock": load_stock(data_dir / "stock.json"),
        "operations": read_json(
            data_dir / "operations.json", OPERATION_FIELDS
        ),
    }


def save_data(data: dict, data_dir: Path = DATA_DIR) -> None:
    """Сохраняет все данные программы."""
    save_materials(data_dir / "materials.json", data["materials"])
    save_warehouses(data_dir / "warehouses.json", data["warehouses"])
    save_stock(data_dir / "stock.json", data["stock"])
    write_json(data_dir / "operations.json", data["operations"])
