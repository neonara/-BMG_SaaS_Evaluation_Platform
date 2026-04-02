"""
apps/social_accounts/urls.py

Mount under /api/v1/auth/social/ in api_router.py
"""
from django.urls import path
from .views import SocialCallbackView, SocialLoginInitView, SocialAccountListView, SocialAccountDisconnectView

urlpatterns = [
    # Step 1 — get the redirect URL
    path("<str:provider>/login/",    SocialLoginInitView.as_view(),    name="social-login-init"),
    # Step 2 — provider calls back here
    path("<str:provider>/callback/", SocialCallbackView.as_view(),     name="social-callback"),
    # Manage linked accounts
    path("accounts/",                SocialAccountListView.as_view(),  name="social-account-list"),
    path("accounts/<str:provider>/", SocialAccountDisconnectView.as_view(), name="social-account-disconnect"),
]
