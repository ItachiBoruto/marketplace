from django.urls import path
from . import views

app_name = "backups"

urlpatterns = [
    path("run/", views.run_backup_view, name="run"),
]
