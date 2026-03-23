"""apps/users/views.py"""
from __future__ import annotations

import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.users.models import User
from apps.users.serializers import (
    CustomTokenObtainPairSerializer,
    DeactivateSerializer,
    ExportRequestSerializer,
    InviteSerializer,
    OTPVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterExternalSerializer,
    RegisterInternalSerializer,
    UserAdminSerializer,
    UserAdminUpdateSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserPublicSerializer,
)
from core.permissions.permissions import IsAdminClient, IsHR, IsSuperAdmin
from core.permissions.roles import Role
from core.throttling import (
    LoginThrottle,
    OTPVerifyThrottle,
    PasswordResetThrottle,
    ExportRequestThrottle,
)


# ── Auth views ───────────────────────────────────────────────────────────────

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    POST /api/auth/token/
    Returns 200 with token pair for active users.
    Returns 202 for internal candidates with status=pending_otp.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            # Check if user exists but needs OTP
            email = request.data.get("email", "")
            try:
                user = User.objects.get(email=email)
                if user.status == "pending_otp":
                    return Response(
                        {
                            "detail": f"OTP sent to {email}. Please verify to complete login.",
                            "requires_otp": True,
                        },
                        status=status.HTTP_202_ACCEPTED,
                    )
            except User.DoesNotExist:
                pass
            raise
        return Response(serializer.validated_data)


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError
        from core.cache.service import blacklist_jwt

        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            blacklist_jwt(token["jti"])
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RegisterExternalView(APIView):
    """POST /api/auth/register/ — B2C external candidate registration."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterExternalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Queue welcome email
        from apps.notifications.tasks import send_notification
        send_notification.delay(
            user_id=str(user.pk),
            notification_type="welcome",
            channel="email",
        )
        return Response(UserPublicSerializer(user).data, status=status.HTTP_201_CREATED)


class RegisterInternalView(APIView):
    """
    POST /api/auth/register/internal/
    Auto-detect tenant from email domain, create account with
    status=pending_otp, send OTP.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterInternalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Resolve tenant by email domain
        from apps.tenants.models import Domain
        tenant = Domain.get_tenant_by_email_domain(email)
        if tenant is None:
            return Response(
                {"error": True, "status_code": 404,
                 "detail": f"No organisation found for domain {email.split('@')[-1]}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create user with pending_otp status
        user = User.objects.create_user(
            email=email,
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data["first_name"],
            last_name=serializer.validated_data["last_name"],
            role=Role.INTERNAL_CANDIDATE,
            status="pending_otp",
        )

        # Generate and send OTP
        from apps.users.otp import generate_and_store
        otp_code = generate_and_store(email)
        from apps.users.tasks import send_otp_email
        send_otp_email.delay(user_id=str(user.pk), otp_code=otp_code)

        return Response(
            {
                "detail": f"OTP sent to {email}. Please verify to activate your account.",
                "requires_otp": True,
            },
            status=status.HTTP_201_CREATED,
        )


class OTPVerifyView(APIView):
    """POST /api/auth/otp/verify/ — verify OTP and return token pair."""
    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["otp_code"]

        from apps.users.otp import generate_and_store, verify
        if not verify(email, code):
            # Regenerate and resend OTP for expired case
            try:
                user = User.objects.get(email=email, status="pending_otp")
                new_code = generate_and_store(email)
                from apps.users.tasks import send_otp_email
                send_otp_email.delay(user_id=str(user.pk), otp_code=new_code)
                detail = "OTP has expired. A new code has been sent."
            except User.DoesNotExist:
                detail = "Invalid OTP code."
            return Response(
                {"error": True, "status_code": 400, "detail": detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email, status="pending_otp")
        except User.DoesNotExist:
            return Response(
                {"error": True, "status_code": 400, "detail": "Invalid OTP code."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Activate account
        user.status = "active"
        user.save(update_fields=["status"])

        # Issue token pair
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        from core.cache.service import register_user_token
        register_user_token(str(user.pk), str(refresh["jti"]))

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password/reset/
    Always returns 200 to prevent email enumeration.
    """
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email, status="active")
            from apps.users.tasks import send_password_reset_email
            send_password_reset_email.delay(user_id=str(user.pk))
        except User.DoesNotExist:
            pass  # Intentional — no email enumeration
        return Response(
            {"detail": "If an account exists, a reset link has been sent."}
        )


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password/reset/confirm/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["password"]

        # Validate token from cache
        from django.core.cache import cache
        user_id = cache.get(f"pwd_reset:{token}")
        if not user_id:
            return Response(
                {"error": True, "status_code": 400, "detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": True, "status_code": 400, "detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        cache.delete(f"pwd_reset:{token}")

        # Revoke all existing tokens
        from core.cache.service import blacklist_all_user_tokens
        blacklist_all_user_tokens(str(user.pk))

        return Response({"detail": "Password has been reset. Please log in again."})


# ── User views ───────────────────────────────────────────────────────────────

class MeView(APIView):
    """GET/PATCH /api/v1/users/me/ — own profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserProfileSerializer(request.user).data)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    /api/v1/users/ — user management.
    Permissions: SA/AC/HR can manage; Manager sees team only.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filter_fields = ["role", "status"]

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.all()
        if user.role == Role.MANAGER:
            # Managers see team only — for now return empty queryset
            # (team scoping implemented in Sprint 3 with sessions)
            return qs.none()
        return qs.order_by("email")

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("partial_update", "update"):
            return UserAdminUpdateSerializer
        return UserAdminSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsHR()]
        if self.action in ("partial_update", "update", "deactivate", "reactivate"):
            return [IsHR()]
        if self.action == "export_data":
            return [IsAuthenticated()]
        if self.action in ("provision_csv", "provision_invite"):
            return [IsAdminClient()]
        return [IsHR()]

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        user = self.get_object()
        serializer = DeactivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if user.status == "deactivated":
            return Response(
                {"detail": "User is already deactivated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.deactivate()
        # Signal handles: token revocation + notification (see signals.py)
        return Response(UserAdminSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="reactivate")
    def reactivate(self, request, pk=None):
        user = self.get_object()
        if user.status != "deactivated":
            return Response(
                {"detail": "User is not deactivated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.reactivate()
        return Response(UserAdminSerializer(user).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="export",
        throttle_classes=[ExportRequestThrottle],
    )
    def export_data(self, request, pk=None):
        user = self.get_object()
        # Allow self-export
        if request.user.pk != user.pk and not IsHR().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = ExportRequestSerializer(
            data=request.data,
            context={"target_user": user},
        )
        serializer.is_valid(raise_exception=True)

        # Use provided email or fall back to user's personal_email
        delivery_email = serializer.validated_data.get("personal_email") or user.personal_email

        # Generate recovery token (30-day link)
        token = secrets.token_urlsafe(32)
        user.recovery_token = token
        user.recovery_expires_at = timezone.now() + timedelta(days=30)
        if delivery_email:
            user.personal_email = delivery_email
        user.save(update_fields=["recovery_token", "recovery_expires_at", "personal_email"])

        # Queue export generation
        from apps.users.tasks import generate_data_export
        generate_data_export.delay(user_id=str(user.pk))

        return Response(
            {"detail": f"Export queued. Download link sent to {delivery_email}."},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="provision/csv",
        permission_classes=[IsAdminClient],
    )
    def provision_csv(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"detail": "file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded_file.size > 5 * 1024 * 1024:
            return Response(
                {"detail": "File too large. Maximum 5 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        send_invitations = request.data.get("send_invitations", True)
        from apps.users.tasks import import_users_from_csv
        task = import_users_from_csv.delay(
            csv_content=uploaded_file.read().decode("utf-8"),
            send_invitations=bool(send_invitations),
        )
        return Response(
            {"task_id": task.id, "detail": "CSV queued for processing."},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="provision/invite",
        permission_classes=[IsHR],
    )
    def provision_invite(self, request):
        serializer = InviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitations = serializer.validated_data["invitations"]

        from apps.users.tasks import send_invitation_email
        for inv in invitations:
            send_invitation_email.delay(
                email=inv["email"],
                role=inv["role"],
            )

        return Response(
            {
                "invited": len(invitations),
                "detail": f"{len(invitations)} invitation(s) sent.",
            },
            status=status.HTTP_202_ACCEPTED,
        )
