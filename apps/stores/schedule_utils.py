"""Utilidades para calcular si un comercio esta abierto."""
from datetime import datetime, time

from django.utils import timezone


def _time_in_range(current, start, end):
    """True si 'current' esta entre start y end (inclusive)."""
    if start is None or end is None:
        return False
    if start <= end:
        return start <= current <= end
    else:
        # Rango que cruza medianoche (ej: 22:00 - 02:00)
        return current >= start or current <= end


def is_store_open(store, method='delivery'):
    """
    Determina si un comercio esta abierto AHORA para un metodo dado.

    Args:
        store: instancia de Store
        method: 'delivery' o 'pickup'

    Returns:
        dict con:
          - is_open: bool
          - reason: str (motivo si cerrado)
          - next_open: str opcional (cuando abre proximo)
    """
    # Si el comercio no tiene horarios configurados -> siempre abierto
    if not store.schedules.exists():
        return {'is_open': True, 'reason': None, 'next_open': None}

    # Si no ofrece delivery, y piden delivery -> cerrado
    if method == 'delivery' and not store.offers_delivery:
        return {
            'is_open': False,
            'reason': 'Este comercio no ofrece delivery.',
            'next_open': None,
        }

    now = timezone.localtime()
    today = now.weekday()  # 0=lunes, 6=domingo
    current_time = now.time()

    schedule = store.schedules.filter(day_of_week=today).first()

    if not schedule:
        # No hay horario para hoy -> se asume abierto
        return {'is_open': True, 'reason': None, 'next_open': None}

    if schedule.is_closed:
        return {
            'is_open': False,
            'reason': 'El comercio está cerrado hoy.',
            'next_open': _find_next_open(store, method, today),
        }

    if method == 'delivery':
        open_t = schedule.delivery_open
        close_t = schedule.delivery_close
    else:
        open_t = schedule.pickup_open
        close_t = schedule.pickup_close

    # Si no hay horario definido para este metodo -> asumir cerrado
    if not open_t or not close_t:
        return {
            'is_open': False,
            'reason': f'Este comercio no atiende {method} hoy.',
            'next_open': _find_next_open(store, method, today),
        }

    if _time_in_range(current_time, open_t, close_t):
        return {'is_open': True, 'reason': None, 'next_open': None}

    return {
        'is_open': False,
        'reason': f'Fuera de horario. Atendemos de {open_t.strftime("%H:%M")} a {close_t.strftime("%H:%M")}.',
        'next_open': _find_next_open(store, method, today),
    }


def _find_next_open(store, method, from_day):
    """Busca el proximo dia en que el comercio abre para este metodo."""
    for offset in range(1, 8):
        day = (from_day + offset) % 7
        schedule = store.schedules.filter(day_of_week=day).first()
        if not schedule or schedule.is_closed:
            continue

        if method == 'delivery' and schedule.delivery_open and schedule.delivery_close:
            day_name = schedule.get_day_of_week_display()
            return f"{day_name} a las {schedule.delivery_open.strftime('%H:%M')}"
        elif method == 'pickup' and schedule.pickup_open and schedule.pickup_close:
            day_name = schedule.get_day_of_week_display()
            return f"{day_name} a las {schedule.pickup_open.strftime('%H:%M')}"

    return None


def get_store_status(store):
    """
    Devuelve un dict resumen con el estado del comercio.

    Returns:
        {
            'has_schedule': bool,
            'pickup': {'is_open': bool, 'reason': str, 'next_open': str},
            'delivery': {'is_open': bool, 'reason': str, 'next_open': str},
            'is_fully_open': bool,  # abierto para pickup y/o delivery
        }
    """
    has_schedule = store.schedules.exists()

    if not has_schedule:
        return {
            'has_schedule': False,
            'pickup': {'is_open': True, 'reason': None, 'next_open': None},
            'delivery': {
                'is_open': store.offers_delivery,
                'reason': None if store.offers_delivery else 'Delivery no disponible',
                'next_open': None,
            },
            'is_fully_open': True,
        }

    pickup_status = is_store_open(store, method='pickup')
    delivery_status = is_store_open(store, method='delivery')

    pickup_info = get_today_schedule_info(store, method='pickup')
    delivery_info = get_today_schedule_info(store, method='delivery')

    pickup_status['today_open'] = pickup_info['open_time']
    pickup_status['today_close'] = pickup_info['close_time']
    pickup_status['is_closed_today'] = pickup_info['is_closed_today']

    delivery_status['today_open'] = delivery_info['open_time']
    delivery_status['today_close'] = delivery_info['close_time']
    delivery_status['is_closed_today'] = delivery_info['is_closed_today']

    return {
        'has_schedule': True,
        'pickup': pickup_status,
        'delivery': delivery_status,
        'is_fully_open': pickup_status['is_open'] or delivery_status['is_open'],
    }


def get_today_schedule_info(store, method='delivery'):
    """
    Devuelve informacion del horario de HOY para un metodo.

    Returns:
        {
            'is_open_now': bool,
            'open_time': time or None,   # hora de apertura de hoy
            'close_time': time or None,  # hora de cierre de hoy
            'is_closed_today': bool,
        }
    """
    result = {
        'is_open_now': False,
        'open_time': None,
        'close_time': None,
        'is_closed_today': False,
    }

    # Sin horarios configurados -> siempre abierto
    if not store.schedules.exists():
        result['is_open_now'] = True
        return result

    now = timezone.localtime()
    today = now.weekday()
    current_time = now.time()

    schedule = store.schedules.filter(day_of_week=today).first()

    if not schedule:
        # No hay horario hoy -> se asume abierto
        result['is_open_now'] = True
        return result

    if schedule.is_closed:
        result['is_closed_today'] = True
        return result

    if method == 'delivery':
        open_t = schedule.delivery_open
        close_t = schedule.delivery_close
    else:
        open_t = schedule.pickup_open
        close_t = schedule.pickup_close

    result['open_time'] = open_t
    result['close_time'] = close_t

    if open_t and close_t:
        if _time_in_range(current_time, open_t, close_t):
            result['is_open_now'] = True

    return result
