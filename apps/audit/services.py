from .models import AuditLog
from .thread_local import get_current_ip, get_current_user


def log_action(action, details, store=None, user=None, ip_address=None):
    """
    Registra una acción de auditoría.

    Si `user` o `ip_address` no se pasan explícitamente, se toman del
    thread local (poblado por AuditMiddleware).
    """
    if user is None:
        user = get_current_user()
    if ip_address is None:
        ip_address = get_current_ip()

    return AuditLog.objects.create(
        user=user,
        store=store,
        action=action,
        details=details,
        ip_address=ip_address,
    )
