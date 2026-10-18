from collections.abc import Iterator

from .materials import Material
from .warehouses import Warehouse


class StockItem:
    """Остаток одного материала на одном складе."""

    def __init__(
        self,
        material: Material,
        warehouse: Warehouse,
        quantity: int = 0,
    ) -> None:
        if quantity < 0:
            raise ValueError("Остаток не может быть меньше нуля")
        self.material = material
        self.warehouse = warehouse
        self._quantity = quantity

    @property
    def quantity(self) -> int:
        """Количество, меняется только через add и remove."""
        return self._quantity

    def can_write_off(self, quantity: int) -> bool:
        """Хватает ли остатка, чтобы списать quantity."""
        return quantity <= self._quantity

    def add(self, quantity: int) -> None:
        """Увеличивает остаток."""
        self._quantity += quantity

    def remove(self, quantity: int) -> None:
        """Уменьшает остаток, если материала хватает."""
        if not self.can_write_off(quantity):
            shortage = quantity - self._quantity
            raise ValueError(
                f"Недостаточно материала на складе, не хватает {shortage}"
            )
        self._quantity -= quantity

    def to_data(self) -> dict:
        """Превращает остаток в запись для JSON."""
        return {
            "material_id": self.material.id,
            "warehouse_id": self.warehouse.id,
            "quantity": self._quantity,
        }

    def __str__(self) -> str:
        return f"{self.material.name}: {self._quantity} {self.material.unit}"


def find_stock_item(
    stock: list[StockItem],
    material: Material,
    warehouse: Warehouse,
) -> StockItem | None:
    """Ищет остаток материала на складе."""
    for item in stock:
        if item.material is material and item.warehouse is warehouse:
            return item
    return None


def get_stock_item(
    stock: list[StockItem],
    material: Material,
    warehouse: Warehouse,
) -> StockItem:
    """Возвращает остаток, если его нет, заводит пустой."""
    item = find_stock_item(stock, material, warehouse)
    if item is None:
        item = StockItem(material, warehouse)
        stock.append(item)
    return item


def get_balance(
    stock: list[StockItem],
    material: Material,
    warehouse: Warehouse,
) -> int:
    """Остаток материала на одном складе."""
    item = find_stock_item(stock, material, warehouse)
    return item.quantity if item else 0


def get_total_balance(stock: list[StockItem], material: Material) -> int:
    """Остаток материала на всех складах вместе."""
    return sum(item.quantity for item in stock if item.material is material)


def get_warehouse_stock(
    stock: list[StockItem],
    warehouse: Warehouse,
) -> list[StockItem]:
    """Непустые остатки на складе."""
    return [
        item
        for item in stock
        if item.warehouse is warehouse and item.quantity > 0
    ]


def get_stock_status(current_balance: int, minimum: int) -> str:
    """Текстовый статус остатка относительно минимума."""
    if current_balance == 0:
        return "Материал закончился, требуется срочный дозаказ"
    elif current_balance < minimum:
        return "Остаток ниже минимального, требуется дозаказ"
    return "Остаток в норме"


def low_stock_materials(
    materials: list[Material],
    stock: list[StockItem],
) -> Iterator[tuple[Material, int]]:
    """Перебирает материалы, которые пора дозаказать."""
    for material in materials:
        total = get_total_balance(stock, material)
        if material.needs_reorder(total):
            yield material, total
