"""Validadores reutilizables para archivos subidos."""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
ALLOWED_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/webp']


def validate_image_size(value):
    """Rechaza imagenes mayores a 5 MB."""
    if value.size > MAX_IMAGE_SIZE:
        mb = MAX_IMAGE_SIZE // (1024 * 1024)
        raise ValidationError(
            _(f'La imagen no puede pesar mas de {mb} MB. '
              f'La tuya pesa {value.size / (1024 * 1024):.1f} MB.')
        )


def validate_image_extension(value):
    """Solo permite jpg, jpeg, png, webp."""
    name = (value.name or '').lower()
    if '.' not in name:
        raise ValidationError(_('El archivo no tiene extension valida.'))
    ext = name.rsplit('.', 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ', '.join(ALLOWED_EXTENSIONS)
        raise ValidationError(_(f'Formato no permitido. Usa: {allowed}'))


def validate_image_content_type(value):
    """Solo permite MIME types de imagen seguros."""
    content_type = getattr(value, 'content_type', '') or ''
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            _('Tipo de archivo no permitido. Solo imagenes JPG, PNG o WebP.')
        )


def validate_image(value):
    """Valida tamaño, extension y content-type."""
    validate_image_size(value)
    validate_image_extension(value)
    validate_image_content_type(value)
