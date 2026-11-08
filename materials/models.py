from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode


class Material(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)
    unit = models.CharField("Единица измерения", max_length=30)
    min_balance = models.PositiveIntegerField("Минимум", default=0)
    slug = models.SlugField(
        "URL-идентификатор", max_length=220, unique=True, editable=False,
    )
    reorder_target = models.GeneratedField(
        expression=models.F("min_balance") * 2,
        output_field=models.PositiveIntegerField(), db_persist=True,
        verbose_name="Целевой запас",
        help_text="Двойной минимальный остаток, вычисляется базой данных.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "материал"
        verbose_name_plural = "материалы"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(unidecode(self.name))[:190] or "material"
            candidate = base
            suffix = 2
            while type(self).objects.filter(slug=candidate).exists():
                candidate = f"{base}-{suffix}"
                suffix += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("materials:by_slug", kwargs={"slug": self.slug})

    def __str__(self):
        return f"{self.name} ({self.unit})"
