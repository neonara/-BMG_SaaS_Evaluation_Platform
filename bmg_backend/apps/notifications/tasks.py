"""apps/notifications/tasks.py"""
from __future__ import annotations
import logging
from celery import shared_task

logger = logging.getLogger("bmg.notifications.tasks")


@shared_task(name="apps.notifications.tasks.send_notification", queue="notif")
def send_notification(user_id: str, notification_type: str, channel: str = "email",
                      payload: dict = None) -> None:
    """Generic notification dispatcher — full implementation in Sprint 3."""
    logger.info("Notification queued user=%s type=%s channel=%s",
                user_id, notification_type, channel)


@shared_task(name="apps.notifications.tasks.notify_hr_new_session", queue="notif")
def notify_hr_new_session(session_id: str) -> None:
    logger.info("Notify HR new session=%s", session_id)


@shared_task(name="apps.notifications.tasks.notify_candidates_session_active", queue="notif")
def notify_candidates_session_active(session_id: str) -> None:
    logger.info("Notify candidates session active=%s", session_id)


@shared_task(name="apps.notifications.tasks.notify_manager_session_rejected", queue="notif")
def notify_manager_session_rejected(session_id: str) -> None:
    logger.info("Notify manager session rejected=%s", session_id)


@shared_task(name="apps.notifications.tasks.notify_candidates_session_cancelled", queue="notif")
def notify_candidates_session_cancelled(session_id: str) -> None:
    logger.info("Notify candidates session cancelled=%s", session_id)


@shared_task(name="apps.notifications.tasks.alert_super_admin_anticheat", queue="notif")
def alert_super_admin_anticheat(attempt_id: str) -> None:
    logger.warning("Anti-cheat alert attempt=%s", attempt_id)
