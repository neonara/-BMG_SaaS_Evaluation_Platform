"""
apps/social_accounts/models.py

Stores the link between a BMG User and their OAuth provider identity.
One user can have one account per provider (Google, LinkedIn).
Lives in TENANT schema.
"""
from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class SocialAccount(models.Model):
    PROVIDER_GOOGLE   = "google"
    PROVIDER_LINKEDIN = "linkedin"
    PROVIDER_CHOICES  = [
        (PROVIDER_GOOGLE,   "Google"),
        (PROVIDER_LINKEDIN, "LinkedIn"),
    ]

    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider         = models.CharField(max_length=20, choices=PROVIDER_CHOICES, db_index=True)
    uid              = models.CharField(max_length=255, db_index=True)
    access_token     = models.TextField(blank=True)
    refresh_token    = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    extra_data       = models.JSONField(default=dict)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = "social_accounts_socialaccount"
        unique_together = [("provider", "uid")]
        indexes         = [models.Index(fields=["user", "provider"])]

    def __str__(self) -> str:
        return f"{self.provider}:{self.uid} → {self.user_id}"

    @property
    def is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return False
        return timezone.now() >= self.token_expires_at

    def update_tokens(self, access_token: str, refresh_token: str = "", expires_in: int | None = None) -> None:
        self.access_token  = access_token
        self.refresh_token = refresh_token or self.refresh_token
        if expires_in:
            self.token_expires_at = timezone.now() + timezone.timedelta(seconds=expires_in)
        self.save(update_fields=["access_token", "refresh_token", "token_expires_at", "updated_at"])
