from collections.abc import Callable
from functools import wraps

from models import Material, Warehouse
from models.materials import (
    add_material,
    find_materials,
    get_material_by_id,
    sort_materials,
)
from models.operations import (
    cancel_operation,
    receive_material,
    transfer_material,
    write_off_material,
)
from models.stock import (
    get_balance,
    get_stock_status,
    get_total_balance,
    get_warehouse_stock,
    low_stock_materials,
)
from models.warehouses import add_warehouse, get_warehouse_by_id
from storage import load_data, save_data
from utils import input_int, input_text


def saves_data(action: Callable[..., None]) -> Callable[..., None]:
    """Декоратор: после успешного действия сохраняет данные."""
    @wraps(action)
    def wrapper(data: dict, *args, **kwargs) -> None:
        action(data, *args, **kwargs)
        save_data(data)
    return wrapper


def print_materials_table(data: dict, materials: list[Material]) -> None:
    """Выводит таблицу материалов с общим остатком."""
    print(f"{'№':>3}  {'Название':<30}{'Остаток':>12}  Статус")
    for material in sort_materials(materials):
        total = get_total_balance(data["stock"], material)
        status = get_stock_status(total, material.min_balance)
        amount = f"{total} {material.unit}"
        print(f"{material.id:>3}  {material.name:<30}{amount:>12}  {status}")


def show_materials(data: dict) -> None:
    """Показывает все материалы."""
    if not data["materials"]:
        print("Материалов пока нет")
        return
    print_materials_table(data, data["materials"])


def search_materials(data: dict) -> None:
    """Поиск материала по части названия."""
    query = input_text("Часть названия: ")
    found = find_materials(data["materials"], query)
    if not found:
        print("Ничего не найдено")
        return
    print_materials_table(data, found)


@saves_data
def create_material(data: dict) -> None:
    """Добавляет новый материал."""
    name = input_text("Название: ")
    unit = input_text("Единица измерения (шт, пачка, л...): ")
    min_balance = input_int("Минимальный остаток: ", min_value=0)
    material = add_material(data["materials"], name, unit, min_balance)
    print(f"Материал добавлен под номером {material.id}")


def show_warehouses(data: dict) -> None:
    """Показывает все склады."""
    if not data["warehouses"]:
        print("Складов пока нет")
        return
    for warehouse in data["warehouses"]:
        positions = len(get_warehouse_stock(data["stock"], warehouse))
        print(f"{warehouse.id:>3}  {warehouse}, позиций: {positions}")


@saves_data
def create_warehouse(data: dict) -> None:
    """Добавляет новый склад."""
    name = input_text("Название склада: ")
    location = input_text("Где находится: ")
    warehouse = add_warehouse(data["warehouses"], name, location)
    print(f"Склад добавлен под номером {warehouse.id}")


def choose_material(data: dict) -> Material:
    """Просит выбрать материал по номеру."""
    for material in sort_materials(data["materials"]):
        print(f"  {material.id}. {material.name}")
    return get_material_by_id(
        data["materials"], input_int("Номер материала: ")
    )


def choose_warehouse(data: dict, prompt: str = "Номер склада: ") -> Warehouse:
    """Просит выбрать склад по номеру."""
    for warehouse in data["warehouses"]:
        print(f"  {warehouse.id}. {warehouse.name}")
    return get_warehouse_by_id(data["warehouses"], input_int(prompt))


def show_warehouse_stock(data: dict) -> None:
    """Показывает, что лежит на выбранном складе."""
    warehouse = choose_warehouse(data)
    items = get_warehouse_stock(data["stock"], warehouse)
    if not items:
        print("Склад пустой")
        return
    for item in items:
        print(f"  {item}")


def print_balance(
    data: dict,
    material: Material,
    warehouse: Warehouse,
) -> None:
    """Выводит остаток после операции."""
    balance = get_balance(data["stock"], material, warehouse)
    total = get_total_balance(data["stock"], material)
    unit = material.unit
    print(f"Остаток на складе: {balance} {unit}, всего: {total} {unit}")
    print(f"Статус: {get_stock_status(total, material.min_balance)}")


@saves_data
def receive(data: dict) -> None:
    """Оформляет приход."""
    material = choose_material(data)
    warehouse = choose_warehouse(data)
    quantity = input_int("Количество: ")
    receive_material(
        data["stock"], data["operations"], material, warehouse, quantity
    )
    print("Приход оформлен")
    print_balance(data, material, warehouse)


@saves_data
def write_off(data: dict) -> None:
    """Оформляет расход."""
    material = choose_material(data)
    warehouse = choose_warehouse(data)
    quantity = input_int("Количество: ")
    write_off_material(
        data["stock"], data["operations"], material, warehouse, quantity
    )
    print("Расход оформлен")
    print_balance(data, material, warehouse)


@saves_data
def transfer(data: dict) -> None:
    """Перемещает материал между складами."""
    material = choose_material(data)
    from_warehouse = choose_warehouse(data, "Со склада: ")
    to_warehouse = choose_warehouse(data, "На склад: ")
    quantity = input_int("Количество: ")
    transfer_material(
        data["stock"], data["operations"], material,
        from_warehouse, to_warehouse, quantity,
    )
    print("Перемещение оформлено")
    print_balance(data, material, to_warehouse)


def show_operations(data: dict) -> None:
    """Показывает историю операций."""
    if not data["operations"]:
        print("Операций пока нет")
        return
    for operation in data["operations"]:
        print(f"  {operation}")


@saves_data
def cancel(data: dict) -> None:
    """Отменяет операцию по номеру."""
    show_operations(data)
    if not data["operations"]:
        return
    operation_id = input_int("Номер операции для отмены: ")
    cancel_operation(data["stock"], data["operations"], operation_id)
    print("Операция отменена, остатки пересчитаны")


def show_low_stock(data: dict) -> None:
    """Показывает материалы, которые пора дозаказать."""
    found = False
    for material, total in low_stock_materials(
        data["materials"], data["stock"]
    ):
        found = True
        print(
            f"{material.id:>3}  {material.name:<30}"
            f"есть {total}, минимум {material.min_balance} {material.unit}"
        )
    if not found:
        print("Всё в норме, дозаказывать ничего не нужно")


MENU = {
    "1": ("Показать материалы", show_materials),
    "2": ("Найти материал по названию", search_materials),
    "3": ("Добавить материал", create_material),
    "4": ("Показать склады", show_warehouses),
    "5": ("Добавить склад", create_warehouse),
    "6": ("Остатки на складе", show_warehouse_stock),
    "7": ("Приход", receive),
    "8": ("Расход", write_off),
    "9": ("Перемещение между складами", transfer),
    "10": ("История операций", show_operations),
    "11": ("Отменить операцию", cancel),
    "12": ("Что пора дозаказать", show_low_stock),
}


def main() -> None:
    """Точка входа: загружает данные и крутит меню."""
    data = load_data()
    try:
        while True:
            print("\n=== Учёт расходных материалов ===")
            for key, (title, _) in MENU.items():
                print(f"{key}. {title}")
            print("0. Выход")
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            if choice not in MENU:
                print("Такого пункта нет")
                continue
            try:
                MENU[choice][1](data)
            except ValueError as error:
                print(f"Ошибка: {error}")
    except (EOFError, KeyboardInterrupt):
        print()
    print("Работа завершена")


if __name__ == "__main__":
    main()
