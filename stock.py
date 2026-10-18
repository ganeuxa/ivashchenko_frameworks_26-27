from collections.abc import Iterator

Stock = dict[tuple[int, int], int]


def get_balance(stock: Stock, material_id: int, warehouse_id: int) -> int:
    """Остаток материала на одном складе."""
    return stock.get((material_id, warehouse_id), 0)


def get_total_balance(stock: Stock, material_id: int) -> int:
    """Остаток материала на всех складах вместе."""
    return sum(
        quantity
        for (stock_material_id, _), quantity in stock.items()
        if stock_material_id == material_id
    )


def get_warehouse_stock(stock: Stock, warehouse_id: int) -> dict[int, int]:
    """Что лежит на складе: номер материала и количество."""
    return {
        material_id: quantity
        for (material_id, stock_warehouse_id), quantity in stock.items()
        if stock_warehouse_id == warehouse_id
    }


def can_write_off(current_balance: int, quantity: int) -> bool:
    """Проверяет, хватает ли остатка для списания."""
    return quantity <= current_balance


def change_balance(
    stock: Stock,
    material_id: int,
    warehouse_id: int,
    delta: int,
) -> int:
    """Меняет остаток на delta и возвращает новый остаток."""
    balance = get_balance(stock, material_id, warehouse_id)
    if delta < 0 and not can_write_off(balance, -delta):
        raise ValueError(
            f"Недостаточно материала на складе, не хватает {-delta - balance}"
        )
    new_balance = balance + delta
    if new_balance == 0:
        stock.pop((material_id, warehouse_id), None)
    else:
        stock[(material_id, warehouse_id)] = new_balance
    return new_balance


def get_stock_status(current_balance: int, minimum: int) -> str:
    """Текстовый статус остатка относительно минимума."""
    if current_balance == 0:
        return "Материал закончился, требуется срочный дозаказ"
    elif current_balance < minimum:
        return "Остаток ниже минимального, требуется дозаказ"
    return "Остаток в норме"


def low_stock_materials(
    materials: dict[int, dict],
    stock: Stock,
) -> Iterator[tuple[int, dict, int]]:
    """Перебирает материалы, которых меньше минимума."""
    for material_id, material in materials.items():
        total = get_total_balance(stock, material_id)
        if total < material["min_balance"]:
            yield material_id, material, total
