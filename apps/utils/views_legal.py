"""Vistas para paginas legales (privacidad, terminos, cookies)."""
from django.shortcuts import render


def privacy_policy(request):
    """Politica de Privacidad."""
    return render(request, "legal/privacy.html", {
        "page_title": "Política de Privacidad",
        "last_updated": "19 de septiembre de 2026",
    })


def terms_conditions(request):
    """Terminos y Condiciones."""
    return render(request, "legal/terms.html", {
        "page_title": "Términos y Condiciones",
        "last_updated": "19 de septiembre de 2026",
    })


def cookie_policy(request):
    """Politica de Cookies."""
    return render(request, "legal/cookies.html", {
        "page_title": "Política de Cookies",
        "last_updated": "19 de septiembre de 2026",
    })
