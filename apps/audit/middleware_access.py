"""Middleware para registrar accesos denegados (404/403)."""
import logging
import re

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Rutas que NO queremos registrar (ruido)
IGNORED_PATTERNS = [
    re.compile(r"^/static/"),
    re.compile(r"^/media/"),
    re.compile(r"^/favicon\.ico"),
    re.compile(r"^/robots\.txt"),
    re.compile(r"^/admin/jsi18n/"),
    re.compile(r"^/__debug__/"),
]


class AccessAuditMiddleware(MiddlewareMixin):
    """Registra intentos de acceso denegados a rutas protegidas."""

    def process_response(self, request, response):
        # Solo registrar 403 y 404 de usuarios autenticados
        if response.status_code not in (403, 404):
            return response

        # Solo si esta autenticado (anonimos generan mucho ruido)
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response

        # Ignorar superusers (tus propios 404 no son sospechosos)
        if request.user.is_superuser:
            return response

        path = request.path

        # Ignorar rutas de ruido
        for pattern in IGNORED_PATTERNS:
            if pattern.match(path):
                return response

        # Registrar en AuditLog
        try:
            from apps.audit.thread_local import get_current_ip
            from apps.audit.models import AuditLog

            AuditLog.objects.create(
                user=request.user,
                store=None,
                action="access_denied",
                details=f"Acceso denegado a: {path} ({response.status_code})",
                ip_address=get_current_ip(),
            )
        except Exception as e:
            logger.exception("Error registrando acceso denegado: %s", e)

        return response
