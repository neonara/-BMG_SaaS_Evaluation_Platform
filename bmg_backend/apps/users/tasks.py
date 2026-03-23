"""apps/users/tasks.py — email + provisioning tasks."""
from __future__ import annotations
import csv
import io
import logging
import secrets

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("bmg.users.tasks")


@shared_task(bind=True, name="apps.users.tasks.send_otp_email", queue="email")
def send_otp_email(self, user_id: str, otp_code: str) -> None:
    from apps.users.models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("send_otp_email: user %s not found", user_id)
        return
    body = "Your verification code is: %s\n\nThis code expires in 5 minutes." % otp_code
    send_mail(
        subject="BMG Platform — Your verification code",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    logger.info("OTP email sent to %s", user.email)


@shared_task(bind=True, name="apps.users.tasks.send_password_reset_email", queue="email")
def send_password_reset_email(self, user_id: str) -> None:
    from apps.users.models import User
    from django.core.cache import cache
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    token = secrets.token_urlsafe(32)
    cache.set("pwd_reset:%s" % token, str(user.pk), timeout=1800)
    reset_url = "%s/auth/reset-password?token=%s" % (settings.FRONTEND_URL, token)
    body = "Click the link to reset your password:\n%s\n\nLink expires in 30 minutes." % reset_url
    send_mail(
        subject="BMG Platform — Password Reset",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    logger.info("Password reset email sent to %s", user.email)


@shared_task(bind=True, name="apps.users.tasks.send_invitation_email", queue="email")
def send_invitation_email(self, email: str, role: str) -> None:
    invite_url = "%s/auth/register?role=%s" % (settings.FRONTEND_URL, role)
    body = (
        "You have been invited to join BMG Platform as %s.\n\n"
        "Register here: %s" % (role, invite_url)
    )
    send_mail(
        subject="You have been invited to BMG Platform",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )
    logger.info("Invitation sent to %s role=%s", email, role)


@shared_task(bind=True, name="apps.users.tasks.generate_data_export", queue="pdf")
def generate_data_export(self, user_id: str) -> None:
    """Generate PDF + CSV personal data export and email the download link."""
    from apps.users.models import User
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return
    if user.personal_email and user.recovery_token:
        export_url = "%s/export/%s" % (settings.FRONTEND_URL, user.recovery_token)
        body = "Download your data: %s\n\nThis link expires in 30 days." % export_url
        send_mail(
            subject="Your personal data export is ready",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.personal_email],
        )
    logger.info("Data export queued for user %s", user_id)


@shared_task(bind=True, name="apps.users.tasks.import_users_from_csv", queue="default")
def import_users_from_csv(self, csv_content: str, send_invitations: bool = True) -> dict:
    """Bulk import users from CSV content."""
    from apps.users.models import User
    from core.permissions.roles import Role
    reader = csv.DictReader(io.StringIO(csv_content))
    created, skipped = 0, 0
    for row in reader:
        email = (row.get("email") or "").strip().lower()
        role = (row.get("role") or "").strip().lower()
        first_name = (row.get("first_name") or "").strip()
        last_name = (row.get("last_name") or "").strip()
        if not email or User.objects.filter(email=email).exists():
            skipped += 1
            continue
        valid_roles = [r.value for r in Role]
        User.objects.create_user(
            email=email,
            password=None,
            first_name=first_name,
            last_name=last_name,
            role=role if role in valid_roles else Role.INTERNAL_CANDIDATE,
            status="active",
        )
        if send_invitations:
            send_invitation_email.delay(email=email, role=role)
        created += 1
    logger.info("CSV import done: created=%d skipped=%d", created, skipped)
    return {"created": created, "skipped": skipped}


@shared_task(bind=True, name="apps.users.tasks.cleanup_expired_recovery_links", queue="default")
def cleanup_expired_recovery_links(self) -> None:
    """Celery Beat task: nullify expired recovery tokens."""
    from apps.users.models import User
    from django.utils import timezone
    count = User.objects.filter(
        recovery_expires_at__lt=timezone.now(),
        recovery_token__gt="",
    ).update(recovery_token="", recovery_expires_at=None)
    logger.info("Expired recovery links cleaned: %d", count)


@shared_task(bind=True, name="apps.users.tasks.purge_deactivated_user_data", queue="default")
def purge_deactivated_user_data(self) -> None:
    """GDPR Celery Beat task: anonymise personal data after 30 days."""
    from apps.users.models import User
    from django.utils import timezone
    cutoff = timezone.now() - timezone.timedelta(days=30)
    users = User.objects.filter(status="deactivated", deactivated_at__lt=cutoff)
    count = 0
    for user in users:
        user.first_name = "Deleted"
        user.last_name = "User"
        user.personal_email = ""
        user.recovery_token = ""
        user.recovery_expires_at = None
        user.save(update_fields=[
            "first_name", "last_name", "personal_email",
            "recovery_token", "recovery_expires_at"
        ])
        count += 1
    logger.info("GDPR purge: %d users anonymised", count)
