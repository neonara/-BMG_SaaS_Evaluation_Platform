# """
# apps/sessions_module/signals.py

# Session status changes happen frequently:
#   pending_validation → active → closed / cancelled

# Every status change must invalidate the session list cache for the tenant
# because HR and Manager views show session lists filtered by status.

# We also fire notifications on key transitions:
#   - created by Manager   → notify HR to validate
#   - validated by HR      → notify all assigned candidates
#   - rejected by HR       → notify Manager
#   - cancelled            → notify all assigned candidates
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.sessions.signals")


# def connect() -> None:
#     from django.db.models.signals import post_save, pre_save
#     from apps.sessions_module.models import Session

#     pre_save.connect(
#         _on_session_pre_save,
#         sender=Session,
#         dispatch_uid="sessions.session.pre_save",
#         weak=False,
#     )
#     post_save.connect(
#         _on_session_post_save,
#         sender=Session,
#         dispatch_uid="sessions.session.post_save",
#         weak=False,
#     )
#     logger.debug("sessions_module signals connected")


# def _on_session_pre_save(sender, instance, **kwargs) -> None:
#     if instance.pk:
#         try:
#             instance._old_status = sender.objects.get(pk=instance.pk).status
#         except sender.DoesNotExist:
#             instance._old_status = None
#     else:
#         instance._old_status = None


# def _on_session_post_save(sender, instance, created: bool, **kwargs) -> None:
#     from core.cache.keys import CacheKey
#     from core.cache.service import invalidate_pattern
#     from django.db import connection

#     ck = CacheKey(connection.schema_name)
#     invalidate_pattern(ck.session_pattern())

#     old_status = getattr(instance, "_old_status", None)
#     new_status = instance.status

#     if created and new_status == "pending_validation":
#         _notify_hr_new_session(instance)

#     elif old_status == "pending_validation" and new_status == "active":
#         _notify_candidates_session_active(instance)

#     elif old_status == "pending_validation" and new_status == "cancelled":
#         _notify_manager_session_rejected(instance)

#     elif old_status == "active" and new_status == "cancelled":
#         _notify_candidates_session_cancelled(instance)


# def _notify_hr_new_session(session) -> None:
#     from apps.notifications.tasks import notify_hr_new_session
#     notify_hr_new_session.delay(session_id=str(session.pk))


# def _notify_candidates_session_active(session) -> None:
#     from apps.notifications.tasks import notify_candidates_session_active
#     notify_candidates_session_active.delay(session_id=str(session.pk))


# def _notify_manager_session_rejected(session) -> None:
#     from apps.notifications.tasks import notify_manager_session_rejected
#     notify_manager_session_rejected.delay(session_id=str(session.pk))


# def _notify_candidates_session_cancelled(session) -> None:
#     from apps.notifications.tasks import notify_candidates_session_cancelled
#     notify_candidates_session_cancelled.delay(session_id=str(session.pk))
