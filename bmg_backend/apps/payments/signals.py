# """
# apps/payments/signals.py

# PAYMENT and INVOICE signals.

# On payment completion:
#   1. Grant PACK_USER_ACCESS to the candidate
#   2. Queue invoice PDF generation
#   3. Notify candidate

# We never cache payment or invoice data — financial records must
# always be read from the DB. No cache keys here.
# """
# from __future__ import annotations

# import logging

# logger = logging.getLogger("bmg.payments.signals")


# def connect() -> None:
#     from django.db.models.signals import post_save, pre_save
#     from apps.payments.models import Payment

#     pre_save.connect(
#         _on_payment_pre_save,
#         sender=Payment,
#         dispatch_uid="payments.payment.pre_save",
#         weak=False,
#     )
#     post_save.connect(
#         _on_payment_post_save,
#         sender=Payment,
#         dispatch_uid="payments.payment.post_save",
#         weak=False,
#     )
#     logger.debug("payments signals connected")


# def _on_payment_pre_save(sender, instance, **kwargs) -> None:
#     if instance.pk:
#         try:
#             instance._old_status = sender.objects.get(pk=instance.pk).status
#         except sender.DoesNotExist:
#             instance._old_status = None
#     else:
#         instance._old_status = None


# def _on_payment_post_save(sender, instance, created: bool, **kwargs) -> None:
#     old_status = getattr(instance, "_old_status", None)

#     if old_status != "completed" and instance.status == "completed":
#         _grant_pack_access(instance)
#         _generate_invoice(instance)
#         _notify_candidate_payment_success(instance)
#         logger.info(
#             "Payment completed — access granted candidate=%s pack=%s",
#             instance.candidate_id,
#             instance.pack_id,
#         )

#     elif old_status != "failed" and instance.status == "failed":
#         _notify_candidate_payment_failed(instance)


# def _grant_pack_access(payment) -> None:
#     from apps.packs.models import PackUserAccess
#     PackUserAccess.objects.get_or_create(
#         pack_id=payment.pack_id,
#         user_id=payment.candidate_id,
#         defaults={"granted_via": "payment", "payment_id": payment.pk},
#     )


# def _generate_invoice(payment) -> None:
#     from apps.payments.tasks import generate_invoice_pdf
#     generate_invoice_pdf.apply_async(
#         args=[str(payment.pk)],
#         queue="pdf",
#     )


# def _notify_candidate_payment_success(payment) -> None:
#     from apps.notifications.tasks import send_notification
#     send_notification.delay(
#         user_id=str(payment.candidate_id),
#         notification_type="payment_completed",
#         channel="email",
#         payload={"pack_id": str(payment.pack_id)},
#     )


# def _notify_candidate_payment_failed(payment) -> None:
#     from apps.notifications.tasks import send_notification
#     send_notification.delay(
#         user_id=str(payment.candidate_id),
#         notification_type="payment_failed",
#         channel="email",
#     )
