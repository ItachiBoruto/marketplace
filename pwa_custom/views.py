from django.shortcuts import render

# Create your views here.


from django.shortcuts import render


def offline_view(request):
    """Pagina que se muestra cuando el usuario esta sin conexion."""
    return render(request, "pwa_custom/offline.html", status=200)
