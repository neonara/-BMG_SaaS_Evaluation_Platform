# """
# apps/results/signals.py

# SHAREABLE_REPORT signals.

# When a report is created, write it to cache immediately (write-through).
# When a report is deleted or its token is invalidated, clear the cache.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.results.signals")


# def connect() -> None:
#     from django.db.models.signals import post_delete, post_save
#     from apps.results.models import ShareableReport

#     post_save.connect(
#         _on_report_save,
#         sender=ShareableReport,
#         dispatch_uid="results.shareablereport.post_save",
#         weak=False,
#     )
#     post_delete.connect(
#         _on_report_delete,
#         sender=ShareableReport,
#         dispatch_uid="results.shareablereport.post_delete",
#         weak=False,
#     )
#     logger.debug("results signals connected")


# def _on_report_save(sender, instance, created: bool, **kwargs) -> None:
#     from core.cache.keys import CacheKey, CacheTTL
#     from core.cache.service import invalidate
#     from django.db import connection
#     from django.core.cache import cache

#     ck = CacheKey(connection.schema_name)
#     key = ck.shareable_report(instance.token)

#     if created:
#         # Write-through: cache immediately so the first public hit is fast
#         cache.set(key, {"token": instance.token, "attempt_id": str(instance.attempt_id)},
#                   timeout=CacheTTL.SHAREABLE_REPORT)
#     else:
#         # Token or expiry changed — invalidate
#         invalidate(key)


# def _on_report_delete(sender, instance, **kwargs) -> None:
#     from core.cache.keys import CacheKey
#     from core.cache.service import invalidate
#     from django.db import connection

#     ck = CacheKey(connection.schema_name)
#     invalidate(ck.shareable_report(instance.token))
