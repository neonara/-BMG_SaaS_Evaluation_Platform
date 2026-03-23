"""apps/users/urls/users.py"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.users.views import MeView, UserViewSet

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="users-me"),
    path("", include(router.urls)),
]
