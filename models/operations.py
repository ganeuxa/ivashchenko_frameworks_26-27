from utils import next_id, now_str

from .materials import Material
from .stock import StockItem, get_stock_item
from .warehouses import Warehouse


class Operation:
    """Движение материала, общий класс для всех операций."""

    operation_type = ""
    title = "Операция"

    def __init__(
        self,
        operation_id: int,
        material: Material,
        warehouse: Warehouse,
        quantity: int,
        date: str,
        is_cancelled: bool = False,
    ) -> None:
        Operation.check_quantity(quantity)
        self.id = operation_id
        self.material = material
        self.warehouse = warehouse
        self.quantity = quantity
        self.date = date
        self.is_cancelled = is_cancelled

    @staticmethod
    def check_quantity(quantity: int) -> None:
        """Проверяет, что количество больше нуля."""
        if quantity <= 0:
            raise ValueError("Количество должно быть больше нуля")

    def apply(self, stock: list[StockItem]) -> None:
        """Проводит операцию по остаткам."""
        raise NotImplementedError

    def revert(self, stock: list[StockItem]) -> None:
        """Возвращает остатки как было до операции."""
        raise NotImplementedError

    def cancel(self, stock: list[StockItem]) -> None:
        """Отменяет операцию, в истории она остаётся."""
        if self.is_cancelled:
            raise ValueError(f"Операция №{self.id} уже отменена")
        self.revert(stock)
        self.is_cancelled = True

    def place(self) -> str:
        """Где прошла операция."""
        return self.warehouse.name

    def to_data(self) -> dict:
        """Превращает операцию в запись для JSON."""
        return {
            "id": self.id,
            "type": self.operation_type,
            "material_id": self.material.id,
            "warehouse_id": self.warehouse.id,
            "target_warehouse_id": None,
            "quantity": self.quantity,
            "date": self.date,
            "is_cancelled": self.is_cancelled,
        }

    def __str__(self) -> str:
        mark = " (отменена)" if self.is_cancelled else ""
        return (
            f"№{self.id} {self.date} {self.title}: {self.material.name}, "
            f"{self.quantity} {self.material.unit}, {self.place()}{mark}"
        )


class Receipt(Operation):
    """Приход материала на склад."""

    operation_type = "receipt"
    title = "Приход"

    def apply(self, stock: list[StockItem]) -> None:
        get_stock_item(stock, self.material, self.warehouse).add(self.quantity)

    def revert(self, stock: list[StockItem]) -> None:
        item = get_stock_item(stock, self.material, self.warehouse)
        item.remove(self.quantity)


class WriteOff(Operation):
    """Расход материала со склада."""

    operation_type = "write_off"
    title = "Расход"

    def apply(self, stock: list[StockItem]) -> None:
        item = get_stock_item(stock, self.material, self.warehouse)
        item.remove(self.quantity)

    def revert(self, stock: list[StockItem]) -> None:
        get_stock_item(stock, self.material, self.warehouse).add(self.quantity)


class Transfer(Operation):
    """Перемещение материала между складами."""

    operation_type = "transfer"
    title = "Перемещение"

    def __init__(
        self,
        operation_id: int,
        material: Material,
        warehouse: Warehouse,
        target_warehouse: Warehouse,
        quantity: int,
        date: str,
        is_cancelled: bool = False,
    ) -> None:
        if warehouse is target_warehouse:
            raise ValueError("Склад отправки и склад назначения совпадают")
        super().__init__(
            operation_id, material, warehouse, quantity, date, is_cancelled
        )
        self.target_warehouse = target_warehouse

    def apply(self, stock: list[StockItem]) -> None:
        source = get_stock_item(stock, self.material, self.warehouse)
        target = get_stock_item(stock, self.material, self.target_warehouse)
        source.remove(self.quantity)
        target.add(self.quantity)

    def revert(self, stock: list[StockItem]) -> None:
        source = get_stock_item(stock, self.material, self.warehouse)
        target = get_stock_item(stock, self.material, self.target_warehouse)
        target.remove(self.quantity)
        source.add(self.quantity)

    def place(self) -> str:
        return f"{self.warehouse.name} -> {self.target_warehouse.name}"

    def to_data(self) -> dict:
        data = super().to_data()
        data["target_warehouse_id"] = self.target_warehouse.id
        return data


OPERATION_CLASSES = {
    cls.operation_type: cls for cls in (Receipt, WriteOff, Transfer)
}


def new_operation_id(operations: list[Operation]) -> int:
    """Следующий номер операции."""
    return next_id(operation.id for operation in operations)


def register_operation(
    stock: list[StockItem],
    operations: list[Operation],
    operation: Operation,
) -> Operation:
    """Проводит операцию и записывает её в историю."""
    operation.apply(stock)
    operations.append(operation)
    return operation


def receive_material(
    stock: list[StockItem],
    operations: list[Operation],
    material: Material,
    warehouse: Warehouse,
    quantity: int,
) -> Operation:
    """Оформляет приход."""
    operation = Receipt(
        new_operation_id(operations), material, warehouse, quantity, now_str()
    )
    return register_operation(stock, operations, operation)


def write_off_material(
    stock: list[StockItem],
    operations: list[Operation],
    material: Material,
    warehouse: Warehouse,
    quantity: int,
) -> Operation:
    """Оформляет расход."""
    operation = WriteOff(
        new_operation_id(operations), material, warehouse, quantity, now_str()
    )
    return register_operation(stock, operations, operation)


def transfer_material(
    stock: list[StockItem],
    operations: list[Operation],
    material: Material,
    from_warehouse: Warehouse,
    to_warehouse: Warehouse,
    quantity: int,
) -> Operation:
    """Оформляет перемещение между складами."""
    operation = Transfer(
        new_operation_id(operations),
        material,
        from_warehouse,
        to_warehouse,
        quantity,
        now_str(),
    )
    return register_operation(stock, operations, operation)


def find_operation_by_id(
    operations: list[Operation],
    operation_id: int,
) -> Operation | None:
    """Ищет операцию по номеру, если нет, возвращает None."""
    for operation in operations:
        if operation.id == operation_id:
            return operation
    return None


def get_material_operations(
    operations: list[Operation],
    material: Material,
) -> list[Operation]:
    """Операции по одному материалу."""
    return [
        operation for operation in operations
        if operation.material is material
    ]


def cancel_operation(
    stock: list[StockItem],
    operations: list[Operation],
    operation_id: int,
) -> Operation:
    """Находит операцию и отменяет её."""
    operation = find_operation_by_id(operations, operation_id)
    if operation is None:
        raise ValueError(f"Операции с номером {operation_id} нет")
    operation.cancel(stock)
    return operation
