"""Однократный перенос ПР7 в управляемые Django таблицы."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from materials.models import Material
from operations.models import Operation
from warehouses.models import Stock, Warehouse


@transaction.atomic
def transfer_legacy(source):
    """Источник открыт только для чтения; непустая цель не перезаписывается."""
    if any(model.objects.exists()
           for model in (Material, Warehouse, Stock, Operation)):
        raise ValueError("Целевые таблицы не пусты. Перенос отменён.")
    uri = Path(source).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        data = {name: list(map(dict, conn.execute(f"SELECT * FROM {name}")))
                for name in ("materials", "warehouses", "stock", "operations")}
    for row in data["materials"]:
        Material.objects.create(**row)
    Warehouse.objects.bulk_create([
        Warehouse(**{**row, "location": row["location"] or ""})
        for row in data["warehouses"]
    ])
    Stock.objects.bulk_create([Stock(**row) for row in data["stock"]])
    operations = []
    for row in data["operations"]:
        row["performed_at"] = timezone.make_aware(
            datetime.strptime(row["performed_at"], "%Y-%m-%d %H:%M"),
        )
        row["status"] = (Operation.Status.CANCELLED
                         if row.pop("is_cancelled")
                         else Operation.Status.POSTED)
        obj = Operation(**row)
        obj.full_clean()
        operations.append(obj)
    Operation.objects.bulk_create(operations)
    return {name: len(rows) for name, rows in data.items()}
