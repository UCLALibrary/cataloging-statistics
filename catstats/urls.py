from django.urls import path
from . import views

urlpatterns = [
    path('report', views.run_report, name='run_report'),
]
