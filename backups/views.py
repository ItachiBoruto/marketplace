# -*- coding: utf-8 -*-
"""
Endpoint para disparar backups desde cron externo (cron-job.org).

Protegido por un token secreto en DBBACKUP_CRON_TOKEN (env var).
"""
import logging
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.management import call_command

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "HEAD"])
def run_backup_view(request):
    """
    Dispara un backup si el token es correcto.

    Uso:
        GET /backups/run/?token=<DBBACKUP_CRON_TOKEN>

    Respuestas:
        200 {"ok": true, "message": "..."}      -> backup exitoso
        400 {"ok": false, "error": "..."}       -> error en backup
        403 {"ok": false, "error": "forbidden"} -> token incorrecto
        503 {"ok": false, "error": "..."}       -> no configurado
    """
    # 1) Verificar que el token este configurado
    expected = os.environ.get("DBBACKUP_CRON_TOKEN", "").strip()
    if not expected:
        logger.error("DBBACKUP_CRON_TOKEN no configurado")
        return JsonResponse(
            {"ok": False, "error": "endpoint no configurado"},
            status=503,
        )

    # 2) Verificar el token recibido
    received = request.GET.get("token", "").strip()
    if received != expected:
        logger.warning("Intento de backup con token invalido desde %s",
                       request.META.get("REMOTE_ADDR"))
        return JsonResponse(
            {"ok": False, "error": "forbidden"},
            status=403,
        )

    # 3) Ejecutar el backup
    try:
        logger.info("Iniciando backup via cron")
        call_command("run_backup", "--clean")
        logger.info("Backup completado via cron")
        return JsonResponse({"ok": True, "message": "backup completado"})
    except Exception as e:
        logger.exception("Error en backup via cron")
        return JsonResponse(
            {"ok": False, "error": str(e)[:200]},
            status=400,
        )
