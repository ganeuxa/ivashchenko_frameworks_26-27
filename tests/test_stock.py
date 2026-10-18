import pytest

from models import Material, StockItem, Warehouse
from models.stock import (
    get_balance,
    get_stock_status,
    get_total_balance,
    low_stock_materials,
)


@pytest.fixture
def paper():
    return Material(1, "Бумага А4", "пачка", 10)


@pytest.fixture
def warehouse():
    return Warehouse(1, "Склад №1", "корпус А")


def test_stock_item_links_objects(paper, warehouse):
    item = StockItem(paper, warehouse, 40)
    assert item.material is paper
    assert item.warehouse is warehouse
    assert str(item) == "Бумага А4: 40 пачка"


def test_quantity_is_read_only(paper, warehouse):
    item = StockItem(paper, warehouse, 40)
    with pytest.raises(AttributeError):
        item.quantity = 100


def test_remove_more_than_balance_forbidden(paper, warehouse):
    item = StockItem(paper, warehouse, 40)
    with pytest.raises(ValueError):
        item.remove(50)
    assert item.quantity == 40


def test_remove_whole_balance(paper, warehouse):
    item = StockItem(paper, warehouse, 40)
    assert item.can_write_off(40)
    item.remove(40)
    assert item.quantity == 0


def test_balances(paper, warehouse):
    second = Warehouse(2, "Склад №2", "корпус Б")
    stock = [StockItem(paper, warehouse, 40), StockItem(paper, second, 15)]
    assert get_balance(stock, paper, warehouse) == 40
    assert get_total_balance(stock, paper) == 55


def test_stock_status():
    assert get_stock_status(0, 10).startswith("Материал закончился")
    assert get_stock_status(5, 10).startswith("Остаток ниже")
    assert get_stock_status(10, 10) == "Остаток в норме"


def test_low_stock_materials(paper, warehouse):
    cartridge = Material(2, "Картридж", "шт", 3)
    stock = [
        StockItem(paper, warehouse, 40),
        StockItem(cartridge, warehouse, 2),
    ]
    low = [material for material, _ in low_stock_materials(
        [paper, cartridge], stock
    )]
    assert low == [cartridge]
