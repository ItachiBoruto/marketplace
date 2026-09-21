"""Obtencion de la tasa BCV con retry y fallback."""
import logging
from datetime import date

import requests
from django.core.cache import cache
from django.utils import timezone
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .models import ExchangeRate

logger = logging.getLogger(__name__)

CACHE_KEY = 'bcv_rate_active'
CACHE_TIMEOUT = 1800  # 30 min
API_URL = 'https://bcv.today/api/v1/rate.json'
REQUEST_TIMEOUT = 5


class BCVTransientError(Exception):
    """Error temporal al consultar BCV (timeout, red, 5xx)."""
    pass


class BCVPermanentError(Exception):
    """Error permanente (4xx, JSON invalido)."""
    pass


# ============================================================
# RETRY: reintenta 3 veces con backoff exponencial
# 1s -> 2s -> 4s (total max ~7s)
# ============================================================
@retry(
    retry=retry_if_exception_type(BCVTransientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True,
)
def _fetch_bcv_raw():
    """Hace la peticion HTTP a BCV con retry."""
    try:
        resp = requests.get(API_URL, timeout=REQUEST_TIMEOUT)
    except (requests.Timeout, requests.ConnectionError) as e:
        # Errores transitorios -> reintentar
        raise BCVTransientError(f"Error de red/timeout: {e}") from e

    if resp.status_code >= 500:
        raise BCVTransientError(f"Servidor BCV respondio {resp.status_code}")

    if resp.status_code >= 400:
        raise BCVPermanentError(f"BCV respondio {resp.status_code}")

    try:
        return resp.json()
    except Exception as e:
        raise BCVPermanentError(f"JSON invalido: {e}") from e


def _parse_bcvtoday(data):
    """Extrae tasa y fecha del formato de bcv.today."""
    if not isinstance(data, dict):
        return None, None

    price = data.get('USD')
    effective = data.get('effective_date') or data.get('date', '')

    real_date = None
    if effective:
        try:
            real_date = date.fromisoformat(str(effective)[:10])
        except Exception:
            real_date = None

    try:
        return float(price), real_date
    except (TypeError, ValueError):
        return None, None


def get_bcv_rate():
    """
    Devuelve la tasa BCV vigente.

    Orden de prioridad:
      1. Tasa manual activa (admin)
      2. Cache (30 min)
      3. API automatica (con retry)
      4. Ultima tasa guardada (fallback)
    """
    # 1. Manual activa (tiene prioridad siempre)
    manual = ExchangeRate.objects.filter(is_active=True, fuente='MANUAL').first()
    if manual:
        return float(manual.valor)

    # 2. Cache
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    # 3. API con retry
    try:
        data = _fetch_bcv_raw()
        rate, real_date = _parse_bcvtoday(data)

        if rate is not None:
            today = timezone.now().date()
            fecha = real_date or today

            ExchangeRate.objects.update_or_create(
                fecha=fecha, fuente='AUTO',
                defaults={'valor': rate, 'notas': 'Fuente: bcv.today'}
            )
            cache.set(CACHE_KEY, rate, CACHE_TIMEOUT)
            logger.info("Tasa BCV actualizada: %.4f", rate)
            return rate
    except (BCVTransientError, BCVPermanentError) as e:
        # Se agotaron los reintentos o error permanente
        logger.warning("No se pudo obtener tasa BCV: %s", e)
    except Exception as e:
        logger.exception("Error inesperado obteniendo BCV: %s", e)

    # 4. Fallback: ultima tasa guardada
    last = ExchangeRate.objects.order_by('-fecha', '-actualizado_en').first()
    if last:
        rate = float(last.valor)
        cache.set(CACHE_KEY, rate, CACHE_TIMEOUT)
        logger.info("Usando tasa BCV de fallback: %.4f (fecha %s)", rate, last.fecha)
        return rate

    return None


def invalidate_cache():
    cache.delete(CACHE_KEY)


def get_active_rate_object():
    manual = ExchangeRate.objects.filter(is_active=True, fuente='MANUAL').first()
    if manual:
        return manual
    return ExchangeRate.objects.order_by('-fecha', '-actualizado_en').first()
