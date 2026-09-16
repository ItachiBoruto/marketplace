"""Validadores para email (comprobacion MX)."""
import logging

from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Cache de dominios verificados (evita consultas DNS repetidas en la misma sesion)
_VERIFIED_DOMAINS_CACHE = set()


def validate_email_mx(email):
    """
    Verifica que el dominio del email tenga registros MX (servidor de correo).
    Si no se puede verificar por problemas de red, NO bloquea (fail-open).
    """
    if not email or "@" not in email:
        raise ValidationError("Correo electronico invalido.")

    domain = email.split("@", 1)[1].lower()

    if domain in _VERIFIED_DOMAINS_CACHE:
        return  # Ya validado antes

    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        if not answers:
            raise ValidationError(
                f"El dominio '{domain}' no parece recibir correos. "
                "Verifica tu direccion."
            )
        _VERIFIED_DOMAINS_CACHE.add(domain)
    except ValidationError:
        raise
    except Exception as e:
        # Si es error de red/DNS temporal, no bloqueamos
        logger.warning("No se pudo verificar MX para %s: %s", domain, e)
