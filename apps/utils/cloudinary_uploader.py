"""Subida a Cloudinary con retry automatico."""
import logging

from django.core.files.storage import default_storage
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class CloudinaryUploadError(Exception):
    """Error al subir a Cloudinary."""
    pass


class CloudinaryTransientError(Exception):
    """Error temporal de Cloudinary (red, 5xx)."""
    pass


# Reintenta 3 veces: 2s -> 4s -> 8s (max ~14s)
@retry(
    retry=retry_if_exception_type(CloudinaryTransientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=10),
    reraise=True,
)
def _save_with_retry(file_obj, name):
    """Intenta guardar en Cloudinary con retry."""
    try:
        return default_storage.save(name, file_obj)
    except Exception as e:
        error_msg = str(e).lower()

        # Errores transitorios -> reintentar
        transient_keywords = ['timeout', 'connection', 'network', 'temporarily', '503', '502', '504']
        if any(kw in error_msg for kw in transient_keywords):
            logger.warning("Error transitorio Cloudinary, reintentando: %s", e)
            raise CloudinaryTransientError(str(e)) from e

        # Errores permanentes (auth, quota, formato invalido) -> no reintentar
        logger.error("Error permanente Cloudinary: %s", e)
        raise CloudinaryUploadError(f"Error subiendo archivo: {e}") from e


def upload_image(file_obj, name):
    """
    Sube una imagen a Cloudinary con retry.
    Re-lanza la excepcion si despues de los reintentos sigue fallando.
    """
    try:
        saved_name = _save_with_retry(file_obj, name)
        logger.info("Imagen subida a Cloudinary: %s", saved_name)
        return saved_name
    except CloudinaryTransientError as e:
        logger.error("Cloudinary fallo tras reintentos: %s", e)
        raise CloudinaryUploadError(
            "No pudimos subir la imagen en este momento. "
            "Intenta de nuevo en unos minutos."
        ) from e
    except CloudinaryUploadError:
        raise
    except Exception as e:
        logger.exception("Error inesperado subiendo a Cloudinary: %s", e)
        raise CloudinaryUploadError(
            "Error subiendo imagen. Intenta de nuevo."
        ) from e
