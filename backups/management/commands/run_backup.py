# -*- coding: utf-8 -*-
"""
Comando personalizado para ejecutar backup + limpieza.

Uso:
    python manage.py run_backup           # backup normal
    python manage.py run_backup --clean  # backup + limpieza de viejos
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ejecuta backup de la base de datos y sube a Dropbox"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Limpia backups viejos segun DBBACKUP_CLEANUP_KEEP",
        )
        parser.add_argument(
            "--compress",
            action="store_true",
            default=True,
            help="Comprime el backup (default: True)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("INICIANDO BACKUP"))
        self.stdout.write(self.style.WARNING("=" * 60))

        try:
            call_command("dbbackup", clean=options["clean"], compress=True)
            self.stdout.write(self.style.SUCCESS("[OK] Backup completado"))
        except Exception as e:
            logger.exception("Error en backup: %s", e)
            self.stdout.write(self.style.ERROR(f"[!] Error: {e}"))
            raise

        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("BACKUP FINALIZADO"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
