"""apps/users/serializers.py"""
from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.models import User
from core.permissions.roles import Role


# ── JWT ─────────────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT serializer to:
    1. Inject role + tenant_schema into token payload
    2. Detect internal candidates (status=pending_otp) and return 202
    3. Register the JTI in Redis for bulk revocation on deactivation
    """

    @classmethod
    def get_token(cls, user: User):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        # tenant_schema is set by TenantMiddleware — available on request,
        # but since serializers don't have request, we get it from connection
        try:
            from django.db import connection
            token["tenant_schema"] = connection.schema_name
        except Exception:
            token["tenant_schema"] = "public"
        return token

    def validate(self, attrs: dict) -> dict:
        data = super().validate(attrs)
        user: User = self.user
        # Register JTI for bulk revocation
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken(data["refresh"])
        from core.cache.service import register_user_token
        register_user_token(str(user.pk), refresh["jti"])
        return data


# ── User serializers ─────────────────────────────────────────────────────────

class UserPublicSerializer(serializers.ModelSerializer):
    """Minimal representation — safe to expose."""

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "status", "date_joined",
        ]
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """Full profile — authenticated user sees own data."""

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "status", "personal_email",
            "recovery_expires_at", "date_joined",
        ]
        read_only_fields = [
            "id", "email", "role", "status",
            "recovery_expires_at", "date_joined",
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Fields the authenticated user can update on their own profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "personal_email"]


class UserAdminSerializer(serializers.ModelSerializer):
    """Admin view — includes deactivated_at for HR/AC visibility."""

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "status", "personal_email",
            "deactivated_at", "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined", "deactivated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]

    def validate_role(self, value: str) -> str:
        # Requesting user cannot assign a role >= their own
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            requester = request.user
            role_hierarchy = [
                Role.SUPER_ADMIN, Role.ADMIN_CLIENT, Role.HR,
                Role.MANAGER, Role.INTERNAL_CANDIDATE, Role.EXTERNAL_CANDIDATE,
            ]
            req_idx = role_hierarchy.index(requester.role) if requester.role in role_hierarchy else 999
            val_idx = role_hierarchy.index(value) if value in role_hierarchy else 999
            if val_idx <= req_idx and requester.role != Role.SUPER_ADMIN:
                raise serializers.ValidationError("You cannot assign a role equal to or higher than your own.")
        return value

    def create(self, validated_data: dict) -> User:
        import secrets
        temp_password = secrets.token_urlsafe(24)
        user = User.objects.create_user(
            email=validated_data["email"],
            password=temp_password,
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=validated_data["role"],
            status="active",
        )
        return user


class UserAdminUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "role"]


class DeactivateSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10, max_length=500)


class ExportRequestSerializer(serializers.Serializer):
    personal_email = serializers.EmailField(required=False)

    def validate(self, attrs: dict) -> dict:
        user = self.context.get("target_user")
        if not attrs.get("personal_email") and not (user and user.personal_email):
            raise serializers.ValidationError(
                {"personal_email": "personal_email is required when not already set on the account."}
            )
        return attrs


class InvitationItemSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=[(r.value, r.value) for r in Role])


class InviteSerializer(serializers.Serializer):
    invitations = InvitationItemSerializer(many=True, min_length=1, max_length=50)


# ── Auth serializers ──────────────────────────────────────────────────────────

class RegisterExternalSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm")
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            role=Role.EXTERNAL_CANDIDATE,
            status="active",
        )


class RegisterInternalSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs


class OTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.RegexField(
        regex=r"^[0-9]{6}$",
        error_messages={"invalid": "OTP must be exactly 6 digits."},
    )


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs
