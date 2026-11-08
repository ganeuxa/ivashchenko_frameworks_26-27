from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Operation(models.Model):
    class Type(models.TextChoices):
        RECEIPT = "receipt", "Приход"
        WRITE_OFF = "write_off", "Расход"
        TRANSFER = "transfer", "Перемещение"

    type = models.CharField(max_length=12, choices=Type.choices)
    material = models.ForeignKey(
        "materials.Material", on_delete=models.PROTECT,
        related_name="operations",
    )
    warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT,
        related_name="operations",
    )
    target_warehouse = models.ForeignKey(
        "warehouses.Warehouse", on_delete=models.PROTECT,
        related_name="incoming_transfers", null=True, blank=True,
    )
    quantity = models.PositiveIntegerField()
    performed_at = models.DateTimeField(default=timezone.now)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-performed_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="operation_positive_quantity",
            ),
            models.CheckConstraint(
                condition=(
                    Q(type="transfer", target_warehouse__isnull=False)
                    & ~Q(warehouse=F("target_warehouse"))
                ) | Q(
                    type__in=["receipt", "write_off"],
                    target_warehouse__isnull=True,
                ), name="operation_valid_target",
            ),
        ]

    @property
    def operation_type(self):
        return self.type

    @property
    def title(self):
        return self.get_type_display()

    @property
    def material_name(self):
        return self.material.name

    @property
    def unit(self):
        return self.material.unit

    @property
    def warehouse_name(self):
        return self.warehouse.name

    @property
    def target_name(self):
        return self.target_warehouse.name if self.target_warehouse else ""

    def __str__(self):
        return f"{self.title} №{self.pk}: {self.material}"
