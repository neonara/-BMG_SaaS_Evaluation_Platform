# """
# apps/packs/signals.py

# Signals for the packs app — public schema, shared across all tenants.
# Pack changes must invalidate the catalogue cache immediately because
# the Vitrine and all external candidates depend on it.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.packs.signals")


# def connect() -> None:
#     from django.db.models.signals import post_delete, post_save
#     from apps.packs.models import Pack, Voucher

#     post_save.connect(
#         _on_pack_change,
#         sender=Pack,
#         dispatch_uid="packs.pack.post_save",
#         weak=False,
#     )
#     post_delete.connect(
#         _on_pack_change,
#         sender=Pack,
#         dispatch_uid="packs.pack.post_delete",
#         weak=False,
#     )
#     post_save.connect(
#         _on_voucher_save,
#         sender=Voucher,
#         dispatch_uid="packs.voucher.post_save",
#         weak=False,
#     )
#     logger.debug("packs signals connected")


# def _on_pack_change(sender, instance, **kwargs) -> None:
#     """
#     Invalidate the full pack catalogue and the individual pack detail.
#     Called on save AND delete — both affect what external candidates see.
#     """
#     from core.cache.keys import CacheKey
#     from core.cache.service import invalidate, invalidate_pattern

#     invalidate_pattern(CacheKey.pack_catalogue_pattern())
#     invalidate(CacheKey.pack_detail(str(instance.pk)))
#     logger.info("Pack cache invalidated pk=%s", instance.pk)


# def _on_voucher_save(sender, instance, created: bool, **kwargs) -> None:
#     """
#     Invalidate the voucher status cache when a voucher is used or expires.
#     This prevents a race condition where a used voucher is served from cache.
#     """
#     from core.cache.keys import CacheKey
#     from core.cache.service import invalidate

#     if not created:
#         invalidate(CacheKey.voucher_status(instance.code))
#         logger.debug("Voucher cache invalidated code=%s", instance.code)
