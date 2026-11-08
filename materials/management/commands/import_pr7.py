import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from db.transfer import transfer_legacy


class Command(BaseCommand):
    help = "Перенос базы ПР7 в пустые таблицы Django без изменения источника"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", default=settings.BASE_DIR / "data/consumables.sqlite",
        )

    def handle(self, *args, **options):
        try:
            counts = transfer_legacy(options["source"])
        except (ValueError, OSError, sqlite3.Error,
                ValidationError, IntegrityError) as exc:
            raise CommandError(str(exc)) from exc
        for table, count in counts.items():
            self.stdout.write(f"{table}: {count}")
