from .thread_local import set_current_request


class AuditMiddleware:
    """Guarda la request actual en un thread local para que las señales la usen."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        try:
            response = self.get_response(request)
        finally:
            set_current_request(None)
        return response
