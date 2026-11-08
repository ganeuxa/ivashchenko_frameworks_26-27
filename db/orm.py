"""Запросы веб-приложения. SQL-слой ПР7 сохранён отдельно для истории."""
from django.db.models import Count, F, Max, Min, Q, Sum

from materials.models import Material
from models.stock import stock_gauge
from operations.models import Operation
from warehouses.models import Stock, Warehouse


def materials_with_totals():
    return Material.objects.annotate(
        total=Sum("stocks__quantity", default=0),
    ).order_by("name")


def gauge_rows(rows):
    return [
        {**row, **stock_gauge(row["total"], row["min_balance"])}
        for row in rows
    ]


def material_rows(queryset):
    return gauge_rows(queryset.values(
        "id", "name", "unit", "min_balance", "total", "slug",
    ))


def related_operations():
    return Operation.objects.with_related()


def material_stock(material_id):
    return Stock.objects.filter(
        material_id=material_id, quantity__gt=0,
    ).order_by("warehouse__name").values(
        "warehouse_id", "quantity", warehouse_name=F("warehouse__name"),
    )


def warehouse_stock(warehouse_id):
    # Сумма считается по всем складам, а не только по выбранному.
    totals = materials_with_totals().filter(
        stocks__warehouse_id=warehouse_id, stocks__quantity__gt=0,
    )
    quantities = dict(Stock.objects.filter(
        warehouse_id=warehouse_id, quantity__gt=0,
    ).values_list("material_id", "quantity"))
    return gauge_rows([
        {"material_id": m.id, "material_name": m.name, "unit": m.unit,
         "min_balance": m.min_balance, "total": m.total,
         "quantity": quantities[m.id]}
        for m in totals
    ])


def warehouse_positions():
    return Warehouse.objects.annotate(positions=Count(
        "stocks", filter=Q(stocks__quantity__gt=0),
    )).order_by("name")


def available_warehouses(material_id, quantity):
    return Warehouse.objects.filter(
        stocks__material_id=material_id, stocks__quantity__gte=quantity,
    ).annotate(quantity=F("stocks__quantity")).order_by("-quantity", "name")


def summary():
    return {
        "materials_count": Material.objects.count(),
        "warehouses_count": Warehouse.objects.count(),
        "operations_count": Operation.objects.posted().aggregate(
            total=Count("id"),
        )["total"],
    }


def shortages():
    return material_rows(
        materials_with_totals().filter(total__lt=F("min_balance")),
    )


def statistics_data(min_consumed):
    active = Operation.objects.posted().order_by()
    by_type = list(active.values(
        "type",
    ).annotate(
        operations_count=Count("id"), first_at=Min("performed_at"),
        last_at=Max("performed_at"),
    ).order_by("-operations_count", "type"))
    for row in by_type:
        row["operation_type"] = row["type"]
        row["title"] = Operation.Type(row["type"]).label
    by_warehouse = Warehouse.objects.annotate(operations_count=Count(
        "operations", filter=Q(operations__status=Operation.Status.POSTED),
    )).order_by("-operations_count", "name")
    valid = Q(operations__type=Operation.Type.WRITE_OFF,
              operations__status=Operation.Status.POSTED)
    consumption = Material.objects.annotate(
        write_offs=Count("operations", filter=valid),
        consumed=Sum("operations__quantity", filter=valid, default=0),
    ).filter(consumed__gte=min_consumed).order_by("-consumed", "name")
    return {"by_type": by_type, "by_warehouse": by_warehouse,
            "consumption": consumption, "min_consumed": min_consumed,
            "status_counts": Operation.objects.aggregate(
                total=Count("id"),
                posted=Count("id", filter=Q(status=Operation.Status.POSTED)),
                cancelled=Count(
                    "id", filter=Q(status=Operation.Status.CANCELLED),
                ),
                drafts=Count("id", filter=Q(status=Operation.Status.DRAFT)),
            )}
