from django.contrib import admin

from .models import Material
from operations.admin import OperationInline
from warehouses.admin import StockInline


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "min_balance", "reorder_target", "slug")
    search_fields = ("name", "unit")
    list_filter = ("unit",)
    ordering = ("name",)
    list_per_page = 20
    readonly_fields = ("slug", "reorder_target")
    inlines = (StockInline, OperationInline)
    fieldsets = (
        ("Материал", {"fields": ("name", "unit")}),
        ("Пополнение", {"fields": ("min_balance", "reorder_target")}),
        ("Адрес страницы", {"fields": ("slug",)}),
    )
