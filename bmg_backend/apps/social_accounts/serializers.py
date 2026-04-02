"""
apps/social_accounts/serializers.py
"""
from __future__ import annotations

from rest_framework import serializers
from .models import SocialAccount


class SocialAccountSerializer(serializers.ModelSerializer):
    """Read-only view of a user's linked social accounts."""
    class Meta:
        model  = SocialAccount
        fields = ["id", "provider", "uid", "created_at", "updated_at"]
        read_only_fields = fields


class OAuthCallbackSerializer(serializers.Serializer):
    """Validates the ?code= and optional ?state= returned by the OAuth provider."""
    code  = serializers.CharField(required=True)
    state = serializers.CharField(required=False, default="")


class SocialLoginResponseSerializer(serializers.Serializer):
    """Response sent back to the frontend after successful OAuth."""
    access         = serializers.CharField()
    refresh        = serializers.CharField()
    user_id        = serializers.UUIDField()
    email          = serializers.EmailField()
    is_new_account = serializers.BooleanField()
