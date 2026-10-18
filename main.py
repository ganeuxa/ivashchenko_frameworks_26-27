from materials import (
    add_material,
    find_materials,
    get_material,
    sort_materials,
)
from operations import (
    OPERATION_NAMES,
    cancel_operation,
    receive_material,
    transfer_material,
    write_off_material,
)
from stock import (
    get_balance,
    get_stock_status,
    get_total_balance,
    get_warehouse_stock,
    low_stock_materials,
)
from storage import load_data, save_data
from utils import input_int, input_text
from warehouses import add_warehouse, get_warehouse


def print_materials_table(data: dict, materials: dict[int, dict]) -> None:
    """Выводит таблицу материалов с общим остатком."""
    print(f"{'№':>3}  {'Название':<30}{'Остаток':>12}  Статус")
    for material_id, material in sort_materials(materials):
        total = get_total_balance(data["stock"], material_id)
        status = get_stock_status(total, material["min_balance"])
        amount = f"{total} {material['unit']}"
        name = material["name"]
        print(f"{material_id:>3}  {name:<30}{amount:>12}  {status}")


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


def create_material(data: dict) -> None:
    """Добавляет новый материал."""
    name = input_text("Название: ")
    unit = input_text("Единица измерения (шт, пачка, л...): ")
    min_balance = input_int("Минимальный остаток: ", min_value=0)
    material_id = add_material(data["materials"], name, unit, min_balance)
    save_data(data)
    print(f"Материал добавлен под номером {material_id}")


def show_warehouses(data: dict) -> None:
    """Показывает все склады."""
    if not data["warehouses"]:
        print("Складов пока нет")
        return
    for warehouse_id, warehouse in data["warehouses"].items():
        positions = len(get_warehouse_stock(data["stock"], warehouse_id))
        print(
            f"{warehouse_id:>3}  {warehouse['name']:<20}"
            f"{warehouse['location']:<25}позиций: {positions}"
        )


def create_warehouse(data: dict) -> None:
    """Добавляет новый склад."""
    name = input_text("Название склада: ")
    location = input_text("Где находится: ")
    warehouse_id = add_warehouse(data["warehouses"], name, location)
    save_data(data)
    print(f"Склад добавлен под номером {warehouse_id}")


def choose_material(data: dict) -> int:
    """Просит выбрать материал по номеру."""
    for material_id, material in sort_materials(data["materials"]):
        print(f"  {material_id}. {material['name']}")
    material_id = input_int("Номер материала: ")
    get_material(data["materials"], material_id)
    return material_id


def choose_warehouse(data: dict, prompt: str = "Номер склада: ") -> int:
    """Просит выбрать склад по номеру."""
    for warehouse_id, warehouse in data["warehouses"].items():
        print(f"  {warehouse_id}. {warehouse['name']}")
    warehouse_id = input_int(prompt)
    get_warehouse(data["warehouses"], warehouse_id)
    return warehouse_id


def show_warehouse_stock(data: dict) -> None:
    """Показывает, что лежит на выбранном складе."""
    warehouse_id = choose_warehouse(data)
    items = get_warehouse_stock(data["stock"], warehouse_id)
    if not items:
        print("Склад пустой")
        return
    for material_id, quantity in items.items():
        material = data["materials"][material_id]
        print(f"  {material['name']:<30}{quantity} {material['unit']}")


def print_balance(data: dict, material_id: int, warehouse_id: int) -> None:
    """Выводит остаток после операции."""
    material = data["materials"][material_id]
    unit = material["unit"]
    balance = get_balance(data["stock"], material_id, warehouse_id)
    total = get_total_balance(data["stock"], material_id)
    print(f"Остаток на складе: {balance} {unit}, всего: {total} {unit}")
    print(f"Статус: {get_stock_status(total, material['min_balance'])}")


def receive(data: dict) -> None:
    """Оформляет приход."""
    material_id = choose_material(data)
    warehouse_id = choose_warehouse(data)
    quantity = input_int("Количество: ")
    receive_material(
        data["stock"], data["operations"], material_id, warehouse_id, quantity
    )
    save_data(data)
    print("Приход оформлен")
    print_balance(data, material_id, warehouse_id)


def write_off(data: dict) -> None:
    """Оформляет расход."""
    material_id = choose_material(data)
    warehouse_id = choose_warehouse(data)
    quantity = input_int("Количество: ")
    write_off_material(
        data["stock"], data["operations"], material_id, warehouse_id, quantity
    )
    save_data(data)
    print("Расход оформлен")
    print_balance(data, material_id, warehouse_id)


def transfer(data: dict) -> None:
    """Перемещает материал между складами."""
    material_id = choose_material(data)
    from_id = choose_warehouse(data, "Со склада: ")
    to_id = choose_warehouse(data, "На склад: ")
    quantity = input_int("Количество: ")
    transfer_material(
        data["stock"], data["operations"], material_id, from_id, to_id,
        quantity,
    )
    save_data(data)
    print("Перемещение оформлено")
    print_balance(data, material_id, to_id)


def show_operations(data: dict) -> None:
    """Показывает историю операций."""
    if not data["operations"]:
        print("Операций пока нет")
        return
    for operation in data["operations"]:
        material = data["materials"].get(operation["material_id"], {})
        warehouse = data["warehouses"].get(operation["warehouse_id"], {})
        place = warehouse.get("name", "?")
        if operation["type"] == "transfer":
            target = data["warehouses"].get(
                operation["target_warehouse_id"], {}
            )
            place = f"{place} -> {target.get('name', '?')}"
        print(
            f"{operation['id']:>3}  {operation['date']}  "
            f"{OPERATION_NAMES.get(operation['type'], '?'):<13}"
            f"{material.get('name', '?'):<30}"
            f"{operation['quantity']:>6}  {place}"
        )


def cancel(data: dict) -> None:
    """Отменяет операцию по номеру."""
    show_operations(data)
    if not data["operations"]:
        return
    operation_id = input_int("Номер операции для отмены: ")
    cancel_operation(data["stock"], data["operations"], operation_id)
    save_data(data)
    print("Операция отменена, остатки пересчитаны")


def show_low_stock(data: dict) -> None:
    """Показывает материалы, которые пора дозаказать."""
    found = False
    for material_id, material, total in low_stock_materials(
        data["materials"], data["stock"]
    ):
        found = True
        print(
            f"{material_id:>3}  {material['name']:<30}"
            f"есть {total}, минимум {material['min_balance']} "
            f"{material['unit']}"
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
