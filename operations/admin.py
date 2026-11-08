from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from .models import Operation
from .services import transition


class OperationInline(admin.TabularInline):
    model = Operation
    fk_name = "material"
    fields = ("type", "warehouse", "target_warehouse", "quantity",
              "performed_at", "status")
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).with_related()


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "material", "warehouse",
                    "target_warehouse", "quantity", "performed_at", "status")
    list_filter = ("status", "type", "warehouse", "performed_at")
    search_fields = ("material__name", "warehouse__name",
                     "target_warehouse__name")
    ordering = ("-performed_at", "-id")
    list_per_page = 20
    list_select_related = ("material", "warehouse", "target_warehouse")
    autocomplete_fields = ("material", "warehouse", "target_warehouse")
    date_hierarchy = "performed_at"
    actions = ("post_selected", "cancel_selected")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != Operation.Status.DRAFT:
            return ("type", "material", "warehouse", "target_warehouse",
                    "quantity", "performed_at", "status")
        return ("status",)

    def has_delete_permission(self, request, obj=None):
        return bool(obj and obj.status == Operation.Status.DRAFT
                    and super().has_delete_permission(request, obj))

    def run_transition(self, request, queryset, target):
        count = 0
        for pk in queryset.order_by("pk").values_list("pk", flat=True):
            try:
                obj = transition(pk, target)
            except (ValidationError, DatabaseError) as exc:
                detail = ("; ".join(exc.messages)
                          if isinstance(exc, ValidationError)
                          else "База занята или нарушены ограничения.")
                self.message_user(request, f"№{pk}: {detail}", messages.ERROR)
            else:
                count += 1
                self.log_change(
                    request, obj, f"Статус: {obj.get_status_display()}",
                )
        self.message_user(request, f"Обработано операций: {count}")

    @admin.action(description="Провести / восстановить выбранные операции",
                  permissions=["change"])
    def post_selected(self, request, queryset):
        self.run_transition(request, queryset, Operation.Status.POSTED)

    @admin.action(description="Отменить выбранные операции",
                  permissions=["change"])
    def cancel_selected(self, request, queryset):
        self.run_transition(request, queryset, Operation.Status.CANCELLED)
