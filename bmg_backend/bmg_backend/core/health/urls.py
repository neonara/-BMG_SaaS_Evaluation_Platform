from django.urls import path
from core.health.views import HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="health_check"),
]
