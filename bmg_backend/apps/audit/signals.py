# """
# apps/audit/signals.py

# AUDIT_LOG signals.

# The audit log is write-only and append-only.
# No cache, no notifications, no side effects.
# The only signal handler here enforces the immutability constraint:
# audit log entries must never be updated or deleted.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.audit.signals")


# def connect() -> None:
#     from django.db.models.signals import pre_delete, pre_save
#     from apps.audit.models import AuditLog

#     pre_save.connect(
#         _guard_audit_immutable,
#         sender=AuditLog,
#         dispatch_uid="audit.auditlog.pre_save",
#         weak=False,
#     )
#     pre_delete.connect(
#         _guard_audit_delete,
#         sender=AuditLog,
#         dispatch_uid="audit.auditlog.pre_delete",
#         weak=False,
#     )
#     logger.debug("audit signals connected")


# def _guard_audit_immutable(sender, instance, **kwargs) -> None:
#     """Prevent updates to existing audit log entries."""
#     if instance.pk:
#         from django.core.exceptions import PermissionDenied
#         raise PermissionDenied(
#             "AuditLog entries are immutable and cannot be modified."
#         )


# def _guard_audit_delete(sender, instance, **kwargs) -> None:
#     """Prevent deletion of audit log entries."""
#     from django.core.exceptions import PermissionDenied
#     raise PermissionDenied(
#         "AuditLog entries cannot be deleted."
#     )
