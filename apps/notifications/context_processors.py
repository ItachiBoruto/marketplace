def notifications_count(request):
    """Inyecta el contador de no leidas en todos los templates."""
    if not request.user.is_authenticated:
        return {"unread_notifications_count": 0}
    try:
        count = request.user.notifications.filter(is_read=False).count()
    except Exception:
        count = 0
    return {"unread_notifications_count": count}
