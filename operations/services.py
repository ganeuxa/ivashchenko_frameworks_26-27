"""Проведение и отмена операций вместе с остатками в одной транзакции."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from .models import Operation
from warehouses.models import Stock


def change_stock(material_id, warehouse_id, delta):
    item, _ = Stock.objects.get_or_create(
        material_id=material_id, warehouse_id=warehouse_id,
    )
    rows = Stock.objects.filter(pk=item.pk)
    if delta < 0:
        rows = rows.filter(quantity__gte=-delta)
    if not rows.update(quantity=F("quantity") + delta):
        raise ValidationError("На складе недостаточно материала.")


@transaction.atomic
def transition(operation_id, target):
    op = Operation.objects.select_for_update().get(pk=operation_id)
    if target not in (Operation.Status.POSTED, Operation.Status.CANCELLED):
        raise ValidationError("Недопустимый переход статуса.")
    if op.status == target:
        raise ValidationError("Операция уже находится в этом статусе.")
    op.full_clean()
    # У черновика и отменённой операции нет влияния на остатки.
    direction = 1 if target == Operation.Status.POSTED else -1
    if Operation.Status.POSTED in (target, op.status):
        if op.type == Operation.Type.RECEIPT:
            change_stock(op.material_id, op.warehouse_id,
                         direction * op.quantity)
        else:
            change_stock(op.material_id, op.warehouse_id,
                         -direction * op.quantity)
            if op.type == Operation.Type.TRANSFER:
                change_stock(op.material_id, op.target_warehouse_id,
                             direction * op.quantity)
    op.status = target
    op.save(update_fields=["status"])
    return op
