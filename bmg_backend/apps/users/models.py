"""
apps/users/models.py
Lives in TENANT schema. Full custom user with OTP + dual-view support.
"""
from __future__ import annotations

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from core.permissions.roles import Role


class UserManager(BaseUserManager):
    def _create_user(self, email: str, password: str, **extra) -> "User":
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str = None, **extra) -> "User":
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        extra.setdefault("role", Role.EXTERNAL_CANDIDATE)
        extra.setdefault("status", "active")
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str, **extra) -> "User":
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.SUPER_ADMIN)
        extra.setdefault("status", "active")
        return self._create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    role = models.CharField(
        max_length=30,
        choices=[(r.value, r.value) for r in Role],
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("pending_otp", "Pending OTP"),
            ("deactivated", "Deactivated"),
        ],
        default="pending_otp",
        db_index=True,
    )

    # Personal email for data export delivery (GDPR)
    personal_email = models.EmailField(blank=True)
    # Recovery token for 30-day data export link
    recovery_token = models.CharField(max_length=64, blank=True)
    recovery_expires_at = models.DateTimeField(null=True, blank=True)
    # Timestamp when account was deactivated (used by GDPR purge task)
    deactivated_at = models.DateTimeField(null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users_user"
        indexes = [
            models.Index(fields=["role", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.role})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def deactivate(self) -> None:
        """Set status to deactivated and record timestamp."""
        self.status = "deactivated"
        self.deactivated_at = timezone.now()
        self.save(update_fields=["status", "deactivated_at"])

    def reactivate(self) -> None:
        """Re-activate a deactivated account."""
        self.status = "active"
        self.deactivated_at = None
        self.recovery_token = ""
        self.recovery_expires_at = None
        self.save(update_fields=["status", "deactivated_at",
                                  "recovery_token", "recovery_expires_at"])
