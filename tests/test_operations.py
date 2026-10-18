import pytest

from operations import (
    cancel_operation,
    receive_material,
    transfer_material,
    write_off_material,
)
from stock import get_balance, get_stock_status, low_stock_materials


def test_receive_material():
    stock, operations = {}, []
    receive_material(stock, operations, 1, 1, 15)
    assert get_balance(stock, 1, 1) == 15
    assert operations[0]["type"] == "receipt"


def test_write_off_more_than_balance_forbidden():
    stock, operations = {(1, 1): 40}, []
    with pytest.raises(ValueError):
        write_off_material(stock, operations, 1, 1, 50)
    assert get_balance(stock, 1, 1) == 40
    assert operations == []


def test_write_off_whole_balance():
    stock, operations = {(1, 1): 40}, []
    write_off_material(stock, operations, 1, 1, 40)
    assert get_balance(stock, 1, 1) == 0


def test_transfer_material():
    stock, operations = {(1, 1): 40}, []
    transfer_material(stock, operations, 1, 1, 2, 10)
    assert get_balance(stock, 1, 1) == 30
    assert get_balance(stock, 1, 2) == 10


def test_cancel_write_off_returns_balance():
    stock, operations = {(1, 1): 40}, []
    operation = write_off_material(stock, operations, 1, 1, 35)
    cancel_operation(stock, operations, operation["id"])
    assert get_balance(stock, 1, 1) == 40
    assert operations == []


def test_stock_status():
    assert get_stock_status(0, 10).startswith("Материал закончился")
    assert get_stock_status(5, 10).startswith("Остаток ниже")
    assert get_stock_status(10, 10) == "Остаток в норме"


def test_low_stock_materials():
    materials = {
        1: {"name": "Бумага", "unit": "пачка", "min_balance": 10},
        2: {"name": "Картридж", "unit": "шт", "min_balance": 3},
    }
    stock = {(1, 1): 40, (2, 1): 2}
    low = [material_id for material_id, _, _ in low_stock_materials(
        materials, stock
    )]
    assert low == [2]
