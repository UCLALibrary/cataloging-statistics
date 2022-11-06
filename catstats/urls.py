from django.urls import path
from . import views

urlpatterns = [
    path("", views.run_report, name="run_report"),
    path("report", views.run_report, name="run_report"),
    path("load_data", views.load_data, name="load_data"),
    path("view_logs", views.view_logs, name="view_logs"),
]
