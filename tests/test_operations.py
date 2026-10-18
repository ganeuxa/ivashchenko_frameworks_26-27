import pytest

from models import Material, Receipt, StockItem, Transfer, Warehouse, WriteOff
from models.operations import (
    cancel_operation,
    receive_material,
    transfer_material,
    write_off_material,
)
from models.stock import get_balance


@pytest.fixture
def paper():
    return Material(1, "Бумага А4", "пачка", 10)


@pytest.fixture
def first():
    return Warehouse(1, "Склад №1", "корпус А")


@pytest.fixture
def second():
    return Warehouse(2, "Склад №2", "корпус Б")


def test_receive_material(paper, first):
    stock, operations = [], []
    operation = receive_material(stock, operations, paper, first, 15)
    assert isinstance(operation, Receipt)
    assert operation.material is paper
    assert get_balance(stock, paper, first) == 15


def test_write_off_more_than_balance_forbidden(paper, first):
    stock, operations = [StockItem(paper, first, 40)], []
    with pytest.raises(ValueError):
        write_off_material(stock, operations, paper, first, 50)
    assert get_balance(stock, paper, first) == 40
    assert operations == []


def test_zero_quantity_forbidden(paper, first):
    with pytest.raises(ValueError):
        WriteOff(1, paper, first, 0, "2026-10-01 10:00")


def test_transfer_material(paper, first, second):
    stock, operations = [StockItem(paper, first, 40)], []
    transfer_material(stock, operations, paper, first, second, 10)
    assert get_balance(stock, paper, first) == 30
    assert get_balance(stock, paper, second) == 10


def test_transfer_to_same_warehouse_forbidden(paper, first):
    with pytest.raises(ValueError):
        Transfer(1, paper, first, first, 5, "2026-10-01 10:00")


def test_cancel_keeps_operation_in_history(paper, first):
    stock, operations = [StockItem(paper, first, 40)], []
    operation = write_off_material(stock, operations, paper, first, 35)
    cancel_operation(stock, operations, operation.id)
    assert get_balance(stock, paper, first) == 40
    assert operations == [operation]
    assert operation.is_cancelled


def test_cancel_twice_forbidden(paper, first):
    stock, operations = [], []
    operation = receive_material(stock, operations, paper, first, 5)
    operation.cancel(stock)
    with pytest.raises(ValueError):
        operation.cancel(stock)


def test_cancel_transfer(paper, first, second):
    stock, operations = [StockItem(paper, first, 40)], []
    operation = transfer_material(stock, operations, paper, first, second, 10)
    operation.cancel(stock)
    assert get_balance(stock, paper, first) == 40
    assert get_balance(stock, paper, second) == 0


def test_operations_str_differs_by_type(paper, first, second):
    receipt = Receipt(1, paper, first, 5, "2026-10-01 10:00")
    transfer = Transfer(2, paper, first, second, 5, "2026-10-01 10:00")
    assert "Приход" in str(receipt)
    assert "Склад №1 -> Склад №2" in str(transfer)
