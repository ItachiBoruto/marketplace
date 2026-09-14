from datetime import date

import requests
from django.core.cache import cache
from django.utils import timezone

from .models import ExchangeRate

CACHE_KEY = 'bcv_rate_active'
CACHE_TIMEOUT = 1800  # 30 min

# Endpoints (en orden de prioridad)
SOURCES = [
    {
        'name': 'bcvtoday',
        'url': 'https://bcv.today/api/v1/rate.json',
    },
    {
        'name': 'dolarapi',
        'url': 'https://ve.dolarapi.com/v1/dolares/oficial',
    },
]


def _parse_bcvtoday(data):
    """Formato: {'USD': 832.4883, 'effective_date': '2026-09-11', 'date': '2026-09-14'}"""
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


def _parse_dolarapi(data):
    """Formato: {'promedio': X, 'fechaActualizacion': '...'}"""
    if not isinstance(data, dict):
        return None, None
    price = data.get('promedio')
    if price is None:
        return None, None
    last_update = data.get('fechaActualizacion', '')
    real_date = None
    if last_update:
        try:
            real_date = date.fromisoformat(str(last_update)[:10])
        except Exception:
            real_date = None
    try:
        return float(price), real_date
    except (TypeError, ValueError):
        return None, None


def _try_source(source):
    try:
        resp = requests.get(source['url'], timeout=6)
        resp.raise_for_status()
        data = resp.json()
        if source['name'] == 'bcvtoday':
            return _parse_bcvtoday(data)
        return _parse_dolarapi(data)
    except Exception:
        return None, None


def get_bcv_rate():
    """
    Devuelve la tasa BCV vigente. Orden de prioridad:
      1. Tasa manual activa (admin)
      2. Fuentes automaticas (bcv.today -> dolarapi)
      3. Ultima tasa guardada (fallback)
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    manual = ExchangeRate.objects.filter(is_active=True, fuente='MANUAL').first()
    if manual:
        rate = float(manual.valor)
        cache.set(CACHE_KEY, rate, CACHE_TIMEOUT)
        return rate

    for source in SOURCES:
        rate, real_date = _try_source(source)
        if rate is not None:
            today = timezone.now().date()
            fecha = real_date or today
            ExchangeRate.objects.update_or_create(
                fecha=fecha,
                fuente='AUTO',
                defaults={'valor': rate, 'notas': f'Fuente: {source["name"]}'}
            )
            cache.set(CACHE_KEY, rate, CACHE_TIMEOUT)
            return rate

    last = ExchangeRate.objects.order_by('-fecha', '-actualizado_en').first()
    if last:
        rate = float(last.valor)
        cache.set(CACHE_KEY, rate, CACHE_TIMEOUT)
        return rate
    return None


def invalidate_cache():
    cache.delete(CACHE_KEY)


def get_active_rate_object():
    manual = ExchangeRate.objects.filter(is_active=True, fuente='MANUAL').first()
    if manual:
        return manual
    return ExchangeRate.objects.order_by('-fecha', '-actualizado_en').first()
