"""Ejecutor simple de tareas en background (thread pool)."""
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Pool con pocos workers para no saturar el plan free
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="async_task")


def run_async(func, *args, **kwargs):
    """
    Ejecuta `func` en un hilo separado.
    Errores NO se propagan al caller.
    """
    try:
        future = _executor.submit(func, *args, **kwargs)

        def _log_error(f):
            try:
                f.result()
            except Exception:
                logger.exception("Error en tarea asincrona: %s", func.__name__)

        future.add_done_callback(_log_error)
    except Exception:
        logger.exception("No se pudo encolar tarea: %s", func.__name__)
