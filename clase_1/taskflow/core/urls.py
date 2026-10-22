from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("health/version/", views.health_version, name="health_version"),
]
