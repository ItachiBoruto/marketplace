from django.urls import path

from . import views_legal

app_name = "legal"

urlpatterns = [
    path("privacidad/", views_legal.privacy_policy, name="privacy"),
    path("terminos/", views_legal.terms_conditions, name="terms"),
    path("cookies/", views_legal.cookie_policy, name="cookies"),
]
