from django.db import models


class Warehouse(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)
    location = models.CharField(
        "Адрес", max_length=300, blank=True, default="",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Stock(models.Model):
    material = models.ForeignKey(
        "materials.Material", on_delete=models.PROTECT, related_name="stocks",
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="stocks",
    )
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["material", "warehouse"], name="unique_material_warehouse",
        )]

    def __str__(self):
        return f"{self.material}: {self.quantity}, {self.warehouse}"
