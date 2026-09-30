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


@require_http_methods(["GET"])
def debug_env_view(request):
    """
    Endpoint TEMPORAL para verificar variables de entorno en Render.
    Remover despues del diagnostico.
    """
    import os
    token_dropbox = os.environ.get("DROPBOX_ACCESS_TOKEN", "") or ""
    token_cron = os.environ.get("DBBACKUP_CRON_TOKEN", "") or ""

    return JsonResponse({
        "DROPBOX_ACCESS_TOKEN_presente": bool(token_dropbox),
        "DROPBOX_ACCESS_TOKEN_longitud": len(token_dropbox),
        "DROPBOX_ACCESS_TOKEN_preview": (token_dropbox[:8] + "..." + token_dropbox[-6:]) if len(token_dropbox) > 14 else "(muy corto)",
        "DBBACKUP_CRON_TOKEN_presente": bool(token_cron),
        "DBBACKUP_CRON_TOKEN_longitud": len(token_cron),
        "DJANGO_SETTINGS_MODULE": os.environ.get("DJANGO_SETTINGS_MODULE", "(no definido)"),
    })
