from utils import next_id


class Warehouse:
    """Склад, где хранятся материалы."""

    def __init__(self, warehouse_id: int, name: str, location: str) -> None:
        self.id = warehouse_id
        self.name = name
        self.location = location

    @classmethod
    def from_data(cls, data: dict) -> "Warehouse":
        """Создаёт склад из записи JSON."""
        return cls(data["id"], data["name"], data["location"])

    def to_data(self) -> dict:
        """Превращает склад в запись для JSON."""
        return {"id": self.id, "name": self.name, "location": self.location}

    def __str__(self) -> str:
        return f"{self.name}, {self.location}"


def add_warehouse(
    warehouses: list[Warehouse],
    name: str,
    location: str,
) -> Warehouse:
    """Создаёт склад и добавляет его в список."""
    existing_names = {warehouse.name.lower() for warehouse in warehouses}
    if name.lower() in existing_names:
        raise ValueError(f"Склад «{name}» уже есть")
    warehouse = Warehouse(
        next_id(warehouse.id for warehouse in warehouses), name, location
    )
    warehouses.append(warehouse)
    return warehouse


def find_warehouse_by_id(
    warehouses: list[Warehouse],
    warehouse_id: int,
) -> Warehouse:
    """Возвращает склад по номеру."""
    for warehouse in warehouses:
        if warehouse.id == warehouse_id:
            return warehouse
    raise ValueError(f"Склада с номером {warehouse_id} нет")
