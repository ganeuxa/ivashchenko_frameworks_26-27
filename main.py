"""Система учёта расходных материалов: начальный сценарий (ПР1).

Сценарий: оформление одной операции (приход или расход) по одному
материалу на одном складе с проверкой остатка.
"""

from datetime import datetime

OPERATION_RECEIPT = "1"
OPERATION_WRITE_OFF = "2"

material_name = "Бумага офисная А4"
unit = "пачка"
warehouse_name = "Склад №1 (корпус А)"
balance = 40
min_balance = 10


def receive_material(current_balance, quantity):
    """Оформляет приход: возвращает новый остаток."""
    return current_balance + quantity


def can_write_off(current_balance, quantity):
    """Проверяет, хватает ли остатка для списания."""
    return quantity <= current_balance


def write_off_material(current_balance, quantity):
    """Оформляет расход: возвращает новый остаток."""
    return current_balance - quantity


def get_stock_status(current_balance, minimum):
    """Возвращает текстовый статус остатка относительно минимума."""
    if current_balance == 0:
        return "Материал закончился, требуется срочный дозаказ"
    elif current_balance < minimum:
        return "Остаток ниже минимального, требуется дозаказ"
    return "Остаток в норме"


def parse_quantity(raw_value):
    """Преобразует введённую строку в количество; 0 при неверном вводе."""
    raw_value = raw_value.strip()
    if raw_value.isdigit():
        return int(raw_value)
    return 0


print("=== Учёт расходных материалов ===")
print(f"Материал: {material_name}")
print(f"Склад: {warehouse_name}")
print(f"Текущий остаток: {balance} ({unit})")
print(f"Минимальный остаток: {min_balance} ({unit})")
print(f"Статус: {get_stock_status(balance, min_balance)}")
print()
print("Операции: 1 — приход, 2 — расход")

operation = input("Выберите операцию: ").strip()
quantity = parse_quantity(input("Количество: "))
operation_date = datetime.now().strftime("%d.%m.%Y %H:%M")

if quantity <= 0:
    print("Ошибка: количество должно быть целым положительным числом")
elif operation == OPERATION_RECEIPT:
    balance = receive_material(balance, quantity)
    print(f"[{operation_date}] Приход: +{quantity} ({unit})")
    print(f"Новый остаток: {balance} ({unit})")
    print(f"Статус: {get_stock_status(balance, min_balance)}")
elif operation == OPERATION_WRITE_OFF:
    if can_write_off(balance, quantity):
        balance = write_off_material(balance, quantity)
        print(f"[{operation_date}] Расход: -{quantity} ({unit})")
        print(f"Новый остаток: {balance} ({unit})")
        print(f"Статус: {get_stock_status(balance, min_balance)}")
    else:
        shortage = quantity - balance
        print(
            f"Ошибка: недостаточно материала на складе, "
            f"не хватает {shortage} ({unit})"
        )
else:
    print("Ошибка: неизвестная операция")
