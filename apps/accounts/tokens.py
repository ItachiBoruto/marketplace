"""Generacion y validacion de tokens firmados para verificacion de email."""
from urllib.parse import quote, unquote

from django.core import signing

# Token expira en 24 horas
TOKEN_MAX_AGE = 60 * 60 * 24  # 24h en segundos
SALT = "email-verification"


def generate_email_verification_token(user):
    """Genera un token firmado con el ID del usuario."""
    return signing.dumps(
        {"user_id": user.pk, "email": user.email},
        salt=SALT,
        compress=True,
    )


def encode_token_for_url(token):
    """URL-encode el token para que sea seguro en URLs (evita problemas con ':' )."""
    return quote(token, safe="")


def decode_token_from_url(encoded_token):
    """Decodifica un token URL-encoded."""
    return unquote(encoded_token)


def verify_email_token(token):
    """
    Verifica un token. Devuelve el dict con los datos o {'error': ...} si falla.
    Acepta el token ya decodificado.
    """
    try:
        data = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE)
        return data
    except signing.SignatureExpired:
        return {"error": "expired"}
    except signing.BadSignature:
        return {"error": "invalid"}
