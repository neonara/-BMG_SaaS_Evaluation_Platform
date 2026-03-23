"""apps/tenants/admin.py"""
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from apps.tenants.models import Domain, Tenant


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ["name", "schema_name", "status", "created_on"]
    list_filter = ["status"]
    search_fields = ["name", "schema_name"]
    readonly_fields = ["id", "schema_name", "created_on"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "email_domain", "tenant", "is_primary"]
    list_filter = ["is_primary"]
    search_fields = ["domain", "email_domain"]
