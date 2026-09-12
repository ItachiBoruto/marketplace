import threading

_thread_locals = threading.local()


def set_current_request(request):
    """Guarda la request actual en el thread local."""
    _thread_locals.request = request


def get_current_request():
    """Devuelve la request actual, o None si no hay."""
    return getattr(_thread_locals, "request", None)


def get_current_user():
    """Devuelve el usuario actual, o None si no hay."""
    request = get_current_request()
    if request is None:
        return None
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return None
    return user


def get_current_ip():
    """Devuelve la IP del cliente actual, o None."""
    request = get_current_request()
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
