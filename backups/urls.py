from django.urls import path
from . import views

app_name = "backups"

urlpatterns = [
    path("run/", views.run_backup_view, name="run"),
    path("debug-env/", views.debug_env_view, name="debug_env"),
]
