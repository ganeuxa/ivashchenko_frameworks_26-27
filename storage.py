import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from models import Material, Operation, StockItem, Transfer, Warehouse
from models.materials import find_material_by_id
from models.operations import OPERATION_CLASSES
from models.warehouses import find_warehouse_by_id

DATA_DIR = Path(__file__).parent / "data"

MATERIAL_FIELDS = {"id", "name", "unit", "min_balance"}
WAREHOUSE_FIELDS = {"id", "name", "location"}
STOCK_FIELDS = {"material_id", "warehouse_id", "quantity"}
OPERATION_FIELDS = {
    "id", "type", "material_id", "warehouse_id", "quantity", "date"
}

T = TypeVar("T")


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


def load_objects(
    path: Path,
    required_fields: set[str],
    build: Callable[[dict], T],
) -> list[T]:
    """Читает записи и делает из них объекты, плохие пропускает."""
    objects = []
    for record in read_json(path, required_fields):
        try:
            objects.append(build(record))
        except ValueError as error:
            print(f"{path.name}: запись пропущена, {error}")
    return objects


def load_materials(path: Path) -> list[Material]:
    """Загружает материалы."""
    return load_objects(path, MATERIAL_FIELDS, Material.from_data)


def load_warehouses(path: Path) -> list[Warehouse]:
    """Загружает склады."""
    return load_objects(path, WAREHOUSE_FIELDS, Warehouse.from_data)


def load_stock(
    path: Path,
    materials: list[Material],
    warehouses: list[Warehouse],
) -> list[StockItem]:
    """Загружает остатки и связывает их с материалами и складами."""
    def build(record: dict) -> StockItem:
        return StockItem(
            find_material_by_id(materials, record["material_id"]),
            find_warehouse_by_id(warehouses, record["warehouse_id"]),
            record["quantity"],
        )

    return load_objects(path, STOCK_FIELDS, build)


def load_operations(
    path: Path,
    materials: list[Material],
    warehouses: list[Warehouse],
) -> list[Operation]:
    """Загружает историю операций и связывает её с объектами."""
    def build(record: dict) -> Operation:
        operation_class = OPERATION_CLASSES.get(record["type"])
        if operation_class is None:
            raise ValueError(f"неизвестный тип операции {record['type']}")
        material = find_material_by_id(materials, record["material_id"])
        warehouse = find_warehouse_by_id(warehouses, record["warehouse_id"])
        is_cancelled = record.get("is_cancelled", False)
        if operation_class is Transfer:
            target = find_warehouse_by_id(
                warehouses, record.get("target_warehouse_id")
            )
            return Transfer(
                record["id"], material, warehouse, target,
                record["quantity"], record["date"], is_cancelled,
            )
        return operation_class(
            record["id"], material, warehouse,
            record["quantity"], record["date"], is_cancelled,
        )

    return load_objects(path, OPERATION_FIELDS, build)


def save_objects(path: Path, objects: list) -> None:
    """Сохраняет объекты через их метод to_data."""
    write_json(path, [item.to_data() for item in objects])


def load_data(data_dir: Path = DATA_DIR) -> dict:
    """Загружает все данные программы."""
    materials = load_materials(data_dir / "materials.json")
    warehouses = load_warehouses(data_dir / "warehouses.json")
    return {
        "materials": materials,
        "warehouses": warehouses,
        "stock": load_stock(data_dir / "stock.json", materials, warehouses),
        "operations": load_operations(
            data_dir / "operations.json", materials, warehouses
        ),
    }


def save_data(data: dict, data_dir: Path = DATA_DIR) -> None:
    """Сохраняет все данные программы."""
    save_objects(data_dir / "materials.json", data["materials"])
    save_objects(data_dir / "warehouses.json", data["warehouses"])
    save_objects(
        data_dir / "stock.json",
        [item for item in data["stock"] if item.quantity > 0],
    )
    save_objects(data_dir / "operations.json", data["operations"])
