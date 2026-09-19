"""Configuracion de Sentry para produccion."""
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


def before_send(event, hint):
    """
    Filtra informacion sensible (PII) antes de enviar a Sentry.
    """
    # Quitar cookies y headers sensibles
    if "request" in event:
        request = event["request"]
        headers = request.get("headers", {})
        for key in list(headers.keys()):
            if key.lower() in ("cookie", "authorization", "x-csrftoken"):
                headers.pop(key, None)

        # Quitar datos del formulario que puedan tener PII
        data = request.get("data", {})
        if isinstance(data, dict):
            for key in list(data.keys()):
                if key.lower() in (
                    "password", "password1", "password2",
                    "payment_reference", "payment_bank",
                    "delivery_address", "phone", "email",
                ):
                    data[key] = "[FILTERED]"

    # Quitar email del usuario
    if "user" in event:
        event["user"].pop("email", None)

    return event


def init_sentry():
    """Inicializa Sentry solo si SENTRY_DSN esta configurado."""
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=0.1,
        send_default_pii=False,
        before_send=before_send,
        ignore_errors=[KeyboardInterrupt],
    )
    return True