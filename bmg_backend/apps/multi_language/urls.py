"""
apps/multi_language/urls.py
Mount under /api/v1/languages/ in api_router.py
"""
from django.urls import path
from .views import (
    LanguageListView,
    LanguageDetailView,
    SetDefaultLanguageView,
    UserLanguagePreferenceView,
)

urlpatterns = [
    path("",                        LanguageListView.as_view(),          name="language-list"),
    path("me/",                     UserLanguagePreferenceView.as_view(), name="language-preference"),
    path("<str:code>/",             LanguageDetailView.as_view(),        name="language-detail"),
    path("<str:code>/set-default/", SetDefaultLanguageView.as_view(),    name="language-set-default"),
]
