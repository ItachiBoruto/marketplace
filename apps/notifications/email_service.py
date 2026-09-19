"""Funciones helper para enviar emails con templates HTML."""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def _base_send(subject, template_name, context, to_emails):
    """Envia un email con HTML + fallback texto plano."""
    if not to_emails:
        return 0

    # Filtrar emails vacios
    to_emails = [e for e in to_emails if e]
    if not to_emails:
        return 0

    try:
        html = render_to_string(template_name, context)
        # Texto plano minimo (sin HTML)
        text = "Mi Marketplace - {}".format(subject)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@marketplace.local")
        msg = EmailMultiAlternatives(subject, text, from_email, to_emails)
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)
        logger.info("Email '%s' enviado a %s", subject, to_emails)
        return len(to_emails)
    except Exception as e:
        logger.exception("Error enviando email '%s': %s", subject, e)
        return 0


def send_new_order_to_admin(order, request=None):
    """Notifica al admin (superuser) que llego un pedido nuevo."""
    from django.contrib.auth.models import User

    admin_emails = list(
        User.objects.filter(is_superuser=True, is_active=True)
        .exclude(email="")
        .values_list("email", flat=True)
    )
    if not admin_emails:
        return 0

    admin_url = ""
    if request:
        admin_url = request.build_absolute_uri(
            reverse("admin:orders_order_change", args=[order.pk])
        )

    return _base_send(
        subject=f"🛒 Nuevo pedido {order.reference_code} por ${order.grand_total:.2f}",
        template_name="emails/new_order_admin.html",
        context={"order": order, "admin_url": admin_url},
        to_emails=admin_emails,
    )


def send_order_item_rejected(order, item, store_name, request=None):
    """Notifica al cliente que un item fue rechazado."""
    if not order.user.email:
        return 0

    # Construir URL sin depender del request (para poder correr en background)
    base_url = getattr(settings, "SITE_URL", "")
    if request:
        order_url = request.build_absolute_uri(reverse("orders:detail", args=[order.pk]))
    elif base_url:
        order_url = f"{base_url.rstrip('/')}{reverse('orders:detail', args=[order.pk])}"
    else:
        order_url = reverse("orders:detail", args=[order.pk])

    return _base_send(
        subject=f"Actualizacion de tu pedido {order.reference_code}",
        template_name="emails/order_rejected_client.html",
        context={
            "order": order,
            "item": item,
            "store_name": store_name,
            "order_url": order_url,
        },
        to_emails=[order.user.email],
    )
