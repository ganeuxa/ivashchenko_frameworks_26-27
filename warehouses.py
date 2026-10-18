from utils import next_id


def add_warehouse(
    warehouses: dict[int, dict],
    name: str,
    location: str,
) -> int:
    """Добавляет склад и возвращает его номер."""
    existing_names = {item["name"].lower() for item in warehouses.values()}
    if name.lower() in existing_names:
        raise ValueError(f"Склад «{name}» уже есть")
    warehouse_id = next_id(warehouses)
    warehouses[warehouse_id] = {"name": name, "location": location}
    return warehouse_id


def get_warehouse(warehouses: dict[int, dict], warehouse_id: int) -> dict:
    """Возвращает склад по номеру."""
    if warehouse_id not in warehouses:
        raise ValueError(f"Склада с номером {warehouse_id} нет")
    return warehouses[warehouse_id]
