"""apps/audit/tasks.py"""
from __future__ import annotations
import logging
from celery import shared_task

logger = logging.getLogger("bmg.audit.tasks")


@shared_task(name="apps.audit.tasks.create_audit_log", queue="default")
def create_audit_log(actor_id: str, action: str, status_code: int = 200) -> None:
    """Create an AUDIT_LOG entry — full implementation in Sprint 3."""
    logger.info("AUDIT actor=%s action=%s status=%d", actor_id, action, status_code)
