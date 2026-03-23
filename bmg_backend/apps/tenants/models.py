"""
apps/tenants/models.py

Tenant and Domain models using django-tenants.
Lives in the PUBLIC schema — shared across all tenants.
"""
import uuid

from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """
    One row per client organisation.
    django-tenants creates / drops a PostgreSQL schema named after
    schema_name when this model is saved / deleted.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default="#1E3A8A")
    status = models.CharField(
        max_length=20,
        choices=[
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("trial", "Trial"),
        ],
        default="trial",
    )
    # auto_create_schema = True means django-tenants creates the PG schema
    # on Tenant.save() automatically.
    auto_create_schema = True
    # Never auto-drop — require explicit DB admin action to drop a schema.
    auto_drop_schema = False

    class Meta:
        db_table = "tenants_tenant"

    def __str__(self) -> str:
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """
    Maps a hostname (e.g. acme.bmg.tn) to a Tenant.
    Also used to detect internal candidates by email domain
    via the email_domain field.
    """

    email_domain = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Email domain for auto-detecting internal candidates (e.g. acme.com).",
    )

    class Meta:
        db_table = "tenants_domain"

    def __str__(self) -> str:
        return self.domain

    @classmethod
    def get_tenant_by_email_domain(cls, email: str) -> "Tenant | None":
        """
        Given an email address, return the Tenant whose email_domain
        matches the domain part of the email.
        Returns None if no match found.
        """
        try:
            domain_part = email.split("@", 1)[1].lower()
        except (IndexError, AttributeError):
            return None
        try:
            return cls.objects.select_related("tenant").get(
                email_domain=domain_part
            ).tenant
        except cls.DoesNotExist:
            return None
