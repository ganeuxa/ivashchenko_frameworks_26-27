from django.core.management.base import BaseCommand
from django.db import transaction

from materials.models import Material


class Command(BaseCommand):
    help = "CRUD через ORM во временной транзакции; данные не сохраняются"

    @transaction.atomic
    def handle(self, *args, **options):
        obj = Material.objects.create(
            name="ПР9: демонстрационный материал", unit="шт", min_balance=1,
        )
        obj = Material.objects.get(pk=obj.pk)
        obj.min_balance = 5
        obj.save(update_fields=["min_balance"])
        obj.refresh_from_db()
        self.stdout.write(
            f"Создание, get(), save(): минимум {obj.min_balance}",
        )
        obj.delete()
        self.stdout.write("Удаление выполнено. Транзакция отменена.")
        transaction.set_rollback(True)
