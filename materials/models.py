from django.db import models


class Material(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)
    unit = models.CharField("Единица измерения", max_length=30)
    min_balance = models.PositiveIntegerField("Минимум", default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.unit})"
