# """
# apps/attempts/signals.py

# TEST_ATTEMPT signals.

# On submission (submitted_at transitions from None to a timestamp):
#   1. Trigger async scoring via Celery
#   2. Update SESSION_ASSIGNMENT status to 'completed'
#   3. Write to cache (write-through, not lazy) since the result
#      is immediately needed by the candidate after submission

# We use pre_save to capture the old submitted_at value so we can
# detect the transition from None → datetime in post_save.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.attempts.signals")


# def connect() -> None:
#     from django.db.models.signals import post_save, pre_save
#     from apps.attempts.models import TestAttempt

#     pre_save.connect(
#         _on_attempt_pre_save,
#         sender=TestAttempt,
#         dispatch_uid="attempts.testattempt.pre_save",
#         weak=False,
#     )
#     post_save.connect(
#         _on_attempt_post_save,
#         sender=TestAttempt,
#         dispatch_uid="attempts.testattempt.post_save",
#         weak=False,
#     )
#     logger.debug("attempts signals connected")


# def _on_attempt_pre_save(sender, instance, **kwargs) -> None:
#     if instance.pk:
#         try:
#             old = sender.objects.get(pk=instance.pk)
#             instance._old_submitted_at = old.submitted_at
#             instance._old_is_flagged = old.is_flagged
#         except sender.DoesNotExist:
#             instance._old_submitted_at = None
#             instance._old_is_flagged = False
#     else:
#         instance._old_submitted_at = None
#         instance._old_is_flagged = False


# def _on_attempt_post_save(sender, instance, created: bool, **kwargs) -> None:
#     old_submitted = getattr(instance, "_old_submitted_at", None)
#     old_flagged = getattr(instance, "_old_is_flagged", False)

#     # Detect submission: submitted_at just set for the first time
#     if instance.submitted_at and not old_submitted:
#         _trigger_scoring(instance)
#         _mark_assignment_complete(instance)

#     # Detect flag change: Super Admin BMG alert
#     if instance.is_flagged and not old_flagged:
#         _alert_super_admin_anticheat(instance)


# def _trigger_scoring(attempt) -> None:
#     """
#     Dispatch scoring to the dedicated Celery queue.
#     The task writes score_pct + result fields back to the attempt row.
#     """
#     from apps.attempts.tasks import score_attempt
#     score_attempt.apply_async(
#         args=[str(attempt.pk)],
#         queue="scoring",
#         countdown=0,  # immediate
#     )
#     logger.info("Scoring queued attempt_id=%s", attempt.pk)


# def _mark_assignment_complete(attempt) -> None:
#     if attempt.session_assignment_id:
#         from apps.sessions_module.models import SessionAssignment
#         SessionAssignment.objects.filter(pk=attempt.session_assignment_id).update(
#             status="completed"
#         )


# def _alert_super_admin_anticheat(attempt) -> None:
#     """
#     Super Admin BMG ONLY receives anti-cheat alerts.
#     HR does NOT receive these notifications.
#     """
#     from apps.notifications.tasks import alert_super_admin_anticheat
#     alert_super_admin_anticheat.delay(attempt_id=str(attempt.pk))
#     logger.warning(
#         "Anti-cheat flag set attempt_id=%s — Super Admin alerted", attempt.pk
#     )
