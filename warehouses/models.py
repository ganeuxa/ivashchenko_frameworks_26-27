from django.db import models


class Warehouse(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)
    location = models.CharField(
        "Адрес", max_length=300, blank=True, default="",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "склад"
        verbose_name_plural = "склады"

    def __str__(self):
        return self.name


class Stock(models.Model):
    material = models.ForeignKey(
        "materials.Material", on_delete=models.PROTECT, related_name="stocks",
        verbose_name="Материал",
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="stocks",
        verbose_name="Склад",
    )
    quantity = models.PositiveIntegerField("Количество", default=0)

    class Meta:
        verbose_name = "остаток"
        verbose_name_plural = "остатки"
        constraints = [models.UniqueConstraint(
            fields=["material", "warehouse"], name="unique_material_warehouse",
        )]

    def __str__(self):
        return f"{self.material}: {self.quantity}, {self.warehouse}"
