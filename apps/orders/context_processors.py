from .exchange import get_bcv_rate


def bcv_rate(request):
    return {"bcv_rate": get_bcv_rate()}
