"""Middleware que evita cache del navegador en respuestas autenticadas."""
import re

from django.utils.deprecation import MiddlewareMixin


# Rutas que SI deben cachearse (para rendimiento)
CACHEABLE_PATTERNS = [
    re.compile(r"^/static/"),
    re.compile(r"^/media/"),
    re.compile(r"^/favicon\.ico"),
]


class NoCacheForAuthenticatedMiddleware(MiddlewareMixin):
    """
    Fuerza al navegador a no cachear paginas HTML de usuarios autenticados.
    Esto evita que al presionar 'atras' vean el contenido de una sesion anterior.
    """

    def process_response(self, request, response):
        # Solo aplicar a usuarios autenticados
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response

        # No aplicar a estaticos
        path = request.path
        for pattern in CACHEABLE_PATTERNS:
            if pattern.match(path):
                return response

        # No tocar respuestas de archivos (imagenes, PDFs, etc.)
        content_type = response.get("Content-Type", "")
        if content_type and not content_type.startswith("text/html"):
            return response

        # Headers anti-cache
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["Vary"] = "Cookie"

        return response
