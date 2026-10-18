from stock import Stock, change_balance
from utils import next_id, now_str

OPERATION_NAMES = {
    "receipt": "Приход",
    "write_off": "Расход",
    "transfer": "Перемещение",
}


def check_quantity(quantity: int) -> None:
    """Проверяет, что количество больше нуля."""
    if quantity <= 0:
        raise ValueError("Количество должно быть больше нуля")


def add_operation(
    operations: list[dict],
    operation_type: str,
    material_id: int,
    warehouse_id: int,
    quantity: int,
    target_warehouse_id: int | None = None,
) -> dict:
    """Записывает операцию в историю."""
    operation = {
        "id": next_id(item["id"] for item in operations),
        "type": operation_type,
        "material_id": material_id,
        "warehouse_id": warehouse_id,
        "target_warehouse_id": target_warehouse_id,
        "quantity": quantity,
        "date": now_str(),
    }
    operations.append(operation)
    return operation


def receive_material(
    stock: Stock,
    operations: list[dict],
    material_id: int,
    warehouse_id: int,
    quantity: int,
) -> dict:
    """Приход материала на склад."""
    check_quantity(quantity)
    change_balance(stock, material_id, warehouse_id, quantity)
    return add_operation(
        operations, "receipt", material_id, warehouse_id, quantity
    )


def write_off_material(
    stock: Stock,
    operations: list[dict],
    material_id: int,
    warehouse_id: int,
    quantity: int,
) -> dict:
    """Расход материала со склада."""
    check_quantity(quantity)
    change_balance(stock, material_id, warehouse_id, -quantity)
    return add_operation(
        operations, "write_off", material_id, warehouse_id, quantity
    )


def transfer_material(
    stock: Stock,
    operations: list[dict],
    material_id: int,
    from_warehouse_id: int,
    to_warehouse_id: int,
    quantity: int,
) -> dict:
    """Перемещение материала с одного склада на другой."""
    check_quantity(quantity)
    if from_warehouse_id == to_warehouse_id:
        raise ValueError("Склад отправки и склад назначения совпадают")
    change_balance(stock, material_id, from_warehouse_id, -quantity)
    change_balance(stock, material_id, to_warehouse_id, quantity)
    return add_operation(
        operations,
        "transfer",
        material_id,
        from_warehouse_id,
        quantity,
        to_warehouse_id,
    )


def find_operation(operations: list[dict], operation_id: int) -> dict:
    """Возвращает операцию по номеру."""
    for operation in operations:
        if operation["id"] == operation_id:
            return operation
    raise ValueError(f"Операции с номером {operation_id} нет")


def cancel_operation(
    stock: Stock,
    operations: list[dict],
    operation_id: int,
) -> dict:
    """Отменяет операцию и возвращает остатки как было."""
    operation = find_operation(operations, operation_id)
    material_id = operation["material_id"]
    warehouse_id = operation["warehouse_id"]
    quantity = operation["quantity"]
    if operation["type"] == "receipt":
        change_balance(stock, material_id, warehouse_id, -quantity)
    elif operation["type"] == "write_off":
        change_balance(stock, material_id, warehouse_id, quantity)
    else:
        target_id = operation["target_warehouse_id"]
        change_balance(stock, material_id, target_id, -quantity)
        change_balance(stock, material_id, warehouse_id, quantity)
    operations.remove(operation)
    return operation
