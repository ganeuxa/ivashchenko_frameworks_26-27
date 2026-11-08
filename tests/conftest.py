import os
from contextlib import closing

import django
import pytest
from django.test.utils import (
    setup_databases, setup_test_environment, teardown_databases,
)

from db.database import get_connection
from db.import_json import import_all
from models import Material, Receipt, StockItem, Transfer, Warehouse, WriteOff
from storage import save_data

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "consumables.settings")
django.setup()
setup_test_environment()


def sample_data() -> dict:
    """Небольшой набор данных для тестов базы и страниц."""
    paper = Material(1, "Бумага А4", "пачка", 10)
    cartridge = Material(2, "Картридж", "шт", 3)
    first = Warehouse(1, "Склад №1", "корпус А")
    second = Warehouse(2, "Склад №2", "")
    return {
        "materials": [paper, cartridge],
        "warehouses": [first, second],
        "stock": [
            StockItem(paper, first, 35),
            StockItem(paper, second, 5),
            StockItem(cartridge, first, 2),
        ],
        "operations": [
            Receipt(1, paper, first, 40, "2026-09-01 10:00"),
            WriteOff(2, paper, first, 5, "2026-09-02 11:30", True),
            Receipt(3, cartridge, first, 2, "2026-09-03 09:00"),
            Transfer(4, paper, first, second, 5, "2026-09-04 12:00"),
        ],
    }


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Временная база SQLite с тестовыми данными."""
    save_data(sample_data(), tmp_path)
    path = tmp_path / "test.sqlite"
    with closing(get_connection(path)) as conn:
        import_all(conn, tmp_path)
        conn.commit()
    monkeypatch.setattr("db.database.DB_PATH", path)
    return path


@pytest.fixture(scope="session")
def django_database():
    config = setup_databases(verbosity=0, interactive=False)
    yield
    teardown_databases(config, verbosity=0)


@pytest.fixture
def orm_db(django_database, db_path):
    from db.transfer import transfer_legacy
    from materials.models import Material as ORMmaterial
    from operations.models import Operation
    from warehouses.models import Stock, Warehouse as ORMwarehouse

    def clear():
        for model in (Operation, Stock, ORMmaterial, ORMwarehouse):
            model.objects.all().delete()

    clear()
    transfer_legacy(db_path)
    yield
    clear()
