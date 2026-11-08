from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client
from django.test.utils import CaptureQueriesContext

from db import orm
from materials.models import Material
from operations.models import Operation
from operations.services import transition
from warehouses.models import Stock

pytestmark = pytest.mark.usefixtures("orm_db")


@pytest.fixture
def admin_client():
    user, _ = get_user_model().objects.get_or_create(
        username="test-pr10-admin",
        defaults={"is_staff": True, "is_superuser": True},
    )
    client = Client()
    client.force_login(user)
    return client


def new_operation(kind="receipt", quantity=3, target=None):
    return Operation.objects.create(
        type=kind, material_id=1, warehouse_id=1,
        target_warehouse_id=target, quantity=quantity,
    )


def test_admin_access_control(admin_client):
    assert Client().get("/admin/").status_code == 302
    response = admin_client.get("/admin/")
    assert response.status_code == 200
    html = response.content.decode()
    for word in ("Материалы", "Склады", "Операции", "Остатки"):
        assert word in html
    user, _ = get_user_model().objects.get_or_create(username="visitor")
    client = Client()
    client.force_login(user)
    assert client.get("/admin/").status_code == 302


@pytest.mark.parametrize("url", [
    "/admin/materials/material/", "/admin/warehouses/warehouse/",
    "/admin/warehouses/stock/", "/admin/operations/operation/",
    "/admin/materials/material/1/change/",
    "/admin/warehouses/warehouse/1/change/",
    "/admin/operations/operation/4/change/",
    "/admin/operations/operation/add/",
])
def test_admin_pages_and_inlines(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_admin_search_filter_and_readonly(admin_client):
    response = admin_client.get("/admin/operations/operation/", {
        "q": "Картридж", "status__exact": Operation.Status.POSTED,
    })
    assert [obj.pk for obj in response.context["cl"].queryset] == [3]
    response = admin_client.get("/admin/operations/operation/4/change/")
    assert "quantity" in response.context["adminform"].readonly_fields
    assert admin_client.post("/admin/operations/operation/4/delete/", {
        "post": "yes",
    }).status_code == 403


def test_admin_creation_produces_draft(admin_client):
    before = Stock.objects.get(material_id=1, warehouse_id=1).quantity
    response = admin_client.post("/admin/operations/operation/add/", {
        "type": "receipt", "material": 1, "warehouse": 1,
        "target_warehouse": "", "quantity": 7,
        "performed_at_0": "2026-11-09", "performed_at_1": "12:00:00",
        "_save": "Сохранить",
    })
    assert response.status_code == 302
    op = Operation.objects.latest("pk")
    assert op.status == Operation.Status.DRAFT
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == before


def test_post_cancel_restore_and_prevent_duplicate():
    op = new_operation()
    assert op.status == Operation.Status.DRAFT
    transition(op.pk, Operation.Status.POSTED)
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 38
    with pytest.raises(ValidationError):
        transition(op.pk, Operation.Status.POSTED)
    transition(op.pk, Operation.Status.CANCELLED)
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 35
    transition(op.pk, Operation.Status.POSTED)
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 38


def test_insufficient_stock_and_transfer_rollback():
    op = new_operation("write_off", 100)
    with pytest.raises(ValidationError):
        transition(op.pk, Operation.Status.POSTED)
    op.refresh_from_db()
    assert op.status == Operation.Status.DRAFT
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 35
    transfer = new_operation("transfer", 10, target=2)
    transition(transfer.pk, Operation.Status.POSTED)
    Stock.objects.filter(material_id=1, warehouse_id=2).update(quantity=0)
    with pytest.raises(ValidationError):
        transition(transfer.pk, Operation.Status.CANCELLED)
    transfer.refresh_from_db()
    assert transfer.status == Operation.Status.POSTED
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 25


def test_admin_actions_and_error_messages(admin_client):
    op = new_operation()
    data = {"action": "post_selected", "_selected_action": [op.pk]}
    response = admin_client.post("/admin/operations/operation/", data,
                                 follow=True)
    assert "Обработано операций: 1" in response.content.decode()
    op.refresh_from_db()
    assert op.status == Operation.Status.POSTED
    with patch("operations.admin.transition", side_effect=DatabaseError()):
        response = admin_client.post("/admin/operations/operation/", data,
                                     follow=True)
    assert "База занята" in response.content.decode()
    assert Stock.objects.get(material_id=1, warehouse_id=1).quantity == 38


def test_slug_generated_field_and_common_context():
    obj = Material.objects.create(name="Новый материал", unit="шт",
                                  min_balance=4)
    obj.refresh_from_db()
    assert obj.slug == "novyi-material"
    assert obj.reorder_target == 8
    obj.min_balance = 7
    obj.save()
    obj.refresh_from_db()
    assert obj.reorder_target == 14
    response = Client().get(obj.get_absolute_url())
    assert response.status_code == 200
    assert response.context["site_material_count"] == 3
    assert Client().get("/materials/no-such-slug/").status_code == 404
    obj.name = "Переименован"
    obj.save()
    assert obj.slug == "novyi-material"
    second = Material.objects.create(name="Новый-материал", unit="шт")
    assert second.slug == "novyi-material-2"


def test_status_queryset_statistics_and_stock_availability():
    op = new_operation("write_off", 30)
    assert Operation.objects.drafts().get(pk=op.pk) == op
    assert Operation.objects.cancelled().count() == 1
    assert Operation.objects.posted().count() == 3
    assert orm.statistics_data(0)["status_counts"] == {
        "total": 5, "posted": 3, "cancelled": 1, "drafts": 1,
    }
    assert orm.available_warehouses(1, 10).count() == 1
    transition(op.pk, Operation.Status.POSTED)
    assert orm.available_warehouses(1, 10).count() == 0
    assert orm.statistics_data(1)["consumption"].get(pk=1).consumed == 30
    transition(op.pk, Operation.Status.CANCELLED)
    assert orm.available_warehouses(1, 10).count() == 1
    assert list(orm.statistics_data(1)["consumption"]) == []
    response = Client().get("/operations/", {"status": "cancelled"})
    assert response.context["page_obj"].paginator.count == 2


def test_query_count_does_not_grow_with_operations(admin_client):
    def count():
        with CaptureQueriesContext(connection) as captured:
            response = admin_client.get("/admin/operations/operation/")
            assert response.status_code == 200
        return len(captured)

    before = count()
    for _ in range(12):
        new_operation()
    assert count() == before


def test_data_migration_preserves_cancelled_records():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    old = [("operations", "0001_initial"), ("materials", "0001_initial"),
           ("warehouses", "0001_initial")]
    try:
        executor.migrate(old)
        old_apps = executor.loader.project_state(old).apps
        legacy = old_apps.get_model("operations", "Operation")
        legacy.objects.filter(pk=1).update(is_cancelled=False)
        legacy.objects.filter(pk=2).update(is_cancelled=True)
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        assert Operation.objects.get(pk=1).status == Operation.Status.POSTED
        assert Operation.objects.get(pk=2).status == Operation.Status.CANCELLED
        assert Operation.objects.count() == 4
        assert Material.objects.exclude(slug="").count() == 2
    finally:
        MigrationExecutor(connection).migrate(latest)
