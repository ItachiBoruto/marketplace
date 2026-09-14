"""Filtro de logging para redactar PII (emails, telefonos) de los mensajes."""
import logging
import re


class PIIRedactionFilter(logging.Filter):
    """Reemplaza emails, telefonos y documentos por [REDACTED] en los logs."""

    EMAIL_RE = re.compile(
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
    )

    # Telefonos venezolanos: +58XXX..., 0412..., 0212... con espacios, guiones o puntos
    PHONE_RE = re.compile(
        r'(\+?58|0)[\s\-.]?(\d{3})[\s\-.]?(\d{3})[\s\-.]?(\d{2})[\s\-.]?(\d{2})'
    )

    # Cedulas/RIF (V-12345678, J-123456789, E-12345678)
    DOC_RE = re.compile(r'\b[VEJP]\-?\d{6,10}\b')

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)
        if record.args:
            try:
                record.args = tuple(
                    self._redact(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
            except Exception:
                pass
        return True

    def _redact(self, text):
        if not isinstance(text, str):
            return text
        text = self.EMAIL_RE.sub('[EMAIL_REDACTED]', text)
        text = self.PHONE_RE.sub('[PHONE_REDACTED]', text)
        text = self.DOC_RE.sub('[DOC_REDACTED]', text)
        return text
