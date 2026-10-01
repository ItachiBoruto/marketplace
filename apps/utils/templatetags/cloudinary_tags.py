# -*- coding: utf-8 -*-
"""
Filtros de template para optimizar URLs de Cloudinary.
"""
from django import template

register = template.Library()


@register.filter
def cloudinary_thumb(url, width=400):
    """
    Optimiza una URL de Cloudinary para thumbnail.

    Agrega transformaciones:
    - w_{width}: redimensiona al ancho especificado
    - f_auto: sirve WebP/AVIF segun el navegador
    - q_auto: compresion perceptual
    - c_fill: recorta a cuadrado (opcional)

    Uso en template:
        {{ product.image.url|cloudinary_thumb:400 }}
        {{ product.image.url|cloudinary_thumb:800 }}
    """
    if not url:
        return ""
    if "res.cloudinary.com" not in url:
        return url  # No es Cloudinary, no tocar

    # Separador: '?' si no tiene query, '&' si ya tiene
    sep = "&" if "?" in url else "?"

    return f"{url}{sep}w_{width},f_auto,q_auto"


@register.filter
def cloudinary_detail(url, width=800):
    """
    Optimiza una URL de Cloudinary para vista de detalle.
    """
    return cloudinary_thumb(url, width)


@register.filter
def cloudinary_hero(url, width=1200):
    """
    Optimiza una URL de Cloudinary para hero/banner.
    """
    return cloudinary_thumb(url, width)
