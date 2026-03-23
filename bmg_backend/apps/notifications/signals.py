# """
# apps/notifications/signals.py

# NOTIFICATION signals.

# When a notification transitions to 'sent' or 'failed',
# log the outcome for monitoring dashboards.
# No cache operations — notification data is write-heavy and not cached.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.notifications.signals")


# def connect() -> None:
#     from django.db.models.signals import post_save
#     from apps.notifications.models import Notification

#     post_save.connect(
#         _on_notification_save,
#         sender=Notification,
#         dispatch_uid="notifications.notification.post_save",
#         weak=False,
#     )
#     logger.debug("notifications signals connected")


# def _on_notification_save(sender, instance, created: bool, **kwargs) -> None:
#     if not created and instance.status == "failed":
#         logger.error(
#             "Notification delivery failed pk=%s type=%s channel=%s",
#             instance.pk,
#             instance.type,
#             instance.channel,
#         )
