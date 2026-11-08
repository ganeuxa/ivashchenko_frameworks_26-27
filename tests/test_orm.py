from io import StringIO
import sqlite3

import pytest
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.test.utils import CaptureQueriesContext

from db import orm
from db.transfer import transfer_legacy
from materials.models import Material
from operations.models import Operation
from warehouses.models import Stock, Warehouse

pytestmark = pytest.mark.usefixtures("orm_db")


def test_transfer_preserves_data_and_refuses_second_import(db_path):
    assert Material.objects.count() == 2
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 35
    op = Operation.objects.get(pk=4)
    assert op.target_warehouse.name == "Склад №2"
    assert op.material.name == "Бумага А4"
    assert Operation.objects.get(pk=2).status == Operation.Status.CANCELLED
    with pytest.raises(ValueError, match="не пусты"):
        transfer_legacy(db_path)
    assert Operation.objects.count() == 4


def test_constraints_and_protected_relations():
    with pytest.raises(ProtectedError):
        Material.objects.get(pk=1).delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        Stock.objects.create(material_id=1, warehouse_id=1, quantity=7)
    with pytest.raises(IntegrityError), transaction.atomic():
        Operation.objects.create(
            type="transfer", material_id=1, warehouse_id=1,
            target_warehouse_id=1, quantity=2,
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Operation.objects.create(
            type="receipt", material_id=1, warehouse_id=1, quantity=0,
        )


def test_totals_empty_objects_and_cancelled_statistics():
    Material.objects.create(name="Пустой", unit="шт", min_balance=1)
    Warehouse.objects.create(name="Пустой склад")
    assert orm.materials_with_totals().get(name="Пустой").total == 0
    assert orm.warehouse_positions().get(name="Пустой склад").positions == 0
    assert orm.warehouse_stock(1)[0]["total"] == 40
    data = orm.statistics_data(1)
    assert list(data["consumption"]) == []
    assert sum(row["operations_count"] for row in data["by_type"]) == 3
    assert any(row["name"] == "Пустой" for row in orm.shortages())


def test_related_operations_use_one_query():
    with CaptureQueriesContext(connection) as captured:
        rows = list(orm.related_operations())
        for row in rows:
            assert row.material_name
            assert row.warehouse_name
            _ = row.target_name
    assert len(captured) == 1


def test_search_filters_sort_and_pagination():
    client = Client()
    for _ in range(23):
        Operation.objects.create(
            type="receipt", material_id=1, warehouse_id=1, quantity=2,
            status=Operation.Status.POSTED,
        )
    params = {"q": "Бумага", "type": "receipt", "sort": "oldest",
              "hide_cancelled": "1", "page": 2}
    response = client.get("/operations/", params)
    page = response.context["page_obj"]
    assert page.number == 2
    assert page.paginator.count == 24
    assert len(page.object_list) == 10
    html = response.content.decode()
    assert "sort=oldest" in html and "hide_cancelled=1" in html
    assert "page=3" in html and "page=1" in html
    for value, expected in (("abc", 1), ("999", 3), ("-1", 3)):
        response = client.get("/operations/", {**params, "page": value})
        assert response.context["page_obj"].number == expected


def test_date_related_filter_and_invalid_parameters():
    client = Client()
    response = client.get("/operations/", {
        "from": "2026-09-04", "to": "2026-09-04", "warehouse": 2,
    })
    assert [op.id for op in response.context["operations"]] == [4]
    response = client.get("/operations/", {
        "from": "bad", "sort": "material__password", "warehouse": "bad",
    })
    assert response.status_code == 200
    assert response.context["errors"]
    assert response.context["sort"] == "newest"
    response = client.get("/operations/", {"hide_cancelled": 1})
    assert response.context["page_obj"].paginator.count == 3
    response = client.get("/materials/", {"q": "Картридж"})
    assert [row["name"] for row in response.context["rows"]] == ["Картридж"]
    assert client.get("/operations/", {"q": "нет такого"}).context[
        "page_obj"
    ].paginator.count == 0


def test_crud_command_does_not_change_data():
    before = list(Material.objects.values())
    call_command("demo_crud", stdout=StringIO())
    assert list(Material.objects.values()) == before


def test_transfer_rolls_back_invalid_source(db_path):
    for model in (Operation, Stock, Material, Warehouse):
        model.objects.all().delete()
    with sqlite3.connect(db_path) as source:
        source.execute("UPDATE operations SET target_warehouse_id = 1 "
                       "WHERE type = 'transfer'")
    with pytest.raises(ValidationError):
        transfer_legacy(db_path)
    assert not Material.objects.exists()
    assert not Warehouse.objects.exists()
    assert not Stock.objects.exists()
    assert not Operation.objects.exists()
