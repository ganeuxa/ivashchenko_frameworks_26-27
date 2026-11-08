from django.contrib import admin

from .models import Stock, Warehouse
from operations.admin import OperationInline


class StockInline(admin.TabularInline):
    model = Stock
    fields = ("material", "warehouse", "quantity")
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "material", "warehouse",
        )


class WarehouseOperationInline(OperationInline):
    fk_name = "warehouse"


class IncomingOperationInline(OperationInline):
    fk_name = "target_warehouse"
    verbose_name_plural = "Входящие перемещения"


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "location")
    search_fields = ("name", "location")
    ordering = ("name",)
    list_per_page = 20
    inlines = (StockInline, WarehouseOperationInline, IncomingOperationInline)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("material", "warehouse", "quantity")
    list_filter = ("warehouse",)
    search_fields = ("material__name", "warehouse__name")
    list_select_related = ("material", "warehouse")
    ordering = ("warehouse__name", "material__name")
    list_per_page = 20
    readonly_fields = ("material", "warehouse", "quantity")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
