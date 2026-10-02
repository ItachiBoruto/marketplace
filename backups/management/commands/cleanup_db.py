# -*- coding: utf-8 -*-
"""
Comando de limpieza segura de la base de datos.

Uso:
    python manage.py cleanup_db                 # Todos los defaults
    python manage.py cleanup_db --dry-run       # Muestra que borraria sin borrar
    python manage.py cleanup_db --sessions      # Solo sesiones expiradas
    python manage.py cleanup_db --axes 90       # Solo axes >90 dias
    python manage.py cleanup_db --notifs 60     # Solo notifs leidas >60 dias
    python manage.py cleanup_db --audit 180     # Solo auditoria >180 dias

Por defecto hace TODO con valores conservadores.
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.management import call_command


class Command(BaseCommand):
    help = "Limpia datos antiguos de la base de datos (segura, reversible)"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo mostrar, no borrar")
        parser.add_argument("--sessions", action="store_true", help="Limpiar sesiones expiradas")
        parser.add_argument("--axes", type=int, default=0, help="Dias para axes (default: 90)")
        parser.add_argument("--notifs", type=int, default=0, help="Dias para notificaciones leidas (default: 60)")
        parser.add_argument("--audit", type=int, default=0, help="Dias para audit log (default: 180)")
        parser.add_argument("--all", action="store_true", help="Ejecutar todas las limpiezas")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Si no se especifica nada -> ejecutar todo
        solo_uno = any([options["sessions"], options["axes"], options["notifs"], options["audit"]])
        hacer_todo = options["all"] or not solo_uno

        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("LIMPIEZA DE BASE DE DATOS"))
        if dry_run:
            self.stdout.write(self.style.WARNING("*** MODO DRY-RUN (no borra nada) ***"))
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write("")

        # 1) Sesiones expiradas (siempre se puede)
        if hacer_todo or options["sessions"]:
            self._clean_sessions(dry_run)

        # 2) Axes access log (intentos de login fallidos viejos)
        if hacer_todo or options["axes"]:
            dias = options["axes"] or 90
            self._clean_axes(dias, dry_run)

        # 3) Notificaciones leidas viejas
        if hacer_todo or options["notifs"]:
            dias = options["notifs"] or 60
            self._clean_notifications(dias, dry_run)

        # 4) Audit log viejo
        if hacer_todo or options["audit"]:
            dias = options["audit"] or 180
            self._clean_audit(dias, dry_run)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("LIMPIEZA COMPLETADA"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

    def _clean_sessions(self, dry_run):
        """Elimina sesiones de Django expiradas."""
        from django.contrib.sessions.models import Session
        from django.utils import timezone

        expiradas = Session.objects.filter(expire_date__lt=timezone.now()).count()
        self.stdout.write(f"  Sesiones expiradas: {expiradas}")
        if not dry_run and expiradas > 0:
            call_command("clearsessions")
            self.stdout.write(self.style.SUCCESS(f"  [OK] Sesiones limpiadas"))
        self.stdout.write("")

    def _clean_axes(self, dias, dry_run):
        """Elimina intentos de login fallidos antiguos."""
        try:
            from axes.models import AccessLog, AccessAttempt
        except ImportError:
            self.stdout.write("  [!] django-axes no instalado, saltando")
            return

        corte = timezone.now() - timedelta(days=dias)

        # AccessLog
        log_count = AccessLog.objects.filter(attempt_time__lt=corte).count()
        self.stdout.write(f"  Axes access log > {dias} dias: {log_count}")

        # AccessAttempt (intentos fallidos)
        attempt_count = AccessAttempt.objects.filter(attempt_time__lt=corte).count()
        self.stdout.write(f"  Axes access attempt > {dias} dias: {attempt_count}")

        if not dry_run:
            if log_count > 0:
                AccessLog.objects.filter(attempt_time__lt=corte).delete()
                self.stdout.write(self.style.SUCCESS(f"  [OK] {log_count} logs borrados"))
            if attempt_count > 0:
                AccessAttempt.objects.filter(attempt_time__lt=corte).delete()
                self.stdout.write(self.style.SUCCESS(f"  [OK] {attempt_count} intentos borrados"))
        self.stdout.write("")

    def _clean_notifications(self, dias, dry_run):
        """Elimina notificaciones LEIDAS con mas de X dias."""
        try:
            from apps.notifications.models import Notification
        except ImportError:
            self.stdout.write("  [!] App notifications no disponible, saltando")
            return

        corte = timezone.now() - timedelta(days=dias)
        count = Notification.objects.filter(is_read=True, created_at__lt=corte).count()
        self.stdout.write(f"  Notificaciones leidas > {dias} dias: {count}")

        if not dry_run and count > 0:
            Notification.objects.filter(is_read=True, created_at__lt=corte).delete()
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count} notificaciones borradas"))
        self.stdout.write("")

    def _clean_audit(self, dias, dry_run):
        """Elimina registros de auditoria con mas de X dias."""
        try:
            from apps.audit.models import AuditLog
        except ImportError:
            self.stdout.write("  [!] App audit no disponible, saltando")
            return

        corte = timezone.now() - timedelta(days=dias)
        count = AuditLog.objects.filter(timestamp__lt=corte).count()
        self.stdout.write(f"  Audit log > {dias} dias: {count}")

        if not dry_run and count > 0:
            AuditLog.objects.filter(timestamp__lt=corte).delete()
            self.stdout.write(self.style.SUCCESS(f"  [OK] {count} registros borrados"))
        self.stdout.write("")
