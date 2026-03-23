"""apps/tenants/serializers.py"""
from rest_framework import serializers

from apps.tenants.models import Domain, Tenant


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "domain", "email_domain", "is_primary"]


class TenantSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id", "name", "schema_name", "status",
            "logo_url", "primary_color", "created_on", "domains",
        ]
        read_only_fields = ["id", "schema_name", "created_on"]


class TenantCreateSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(write_only=True, help_text="Primary hostname, e.g. acme.bmg.tn")
    email_domain = serializers.CharField(
        write_only=True,
        required=False,
        default="",
        help_text="Email domain for internal candidate detection, e.g. acme.com",
    )

    class Meta:
        model = Tenant
        fields = [
            "name", "schema_name", "status",
            "logo_url", "primary_color",
            "domain", "email_domain",
        ]

    def validate_schema_name(self, value: str) -> str:
        import re
        if not re.match(r"^[a-z][a-z0-9_]{1,62}$", value):
            raise serializers.ValidationError(
                "schema_name must be lowercase snake_case, 2–63 chars."
            )
        if Tenant.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError("A tenant with this schema_name already exists.")
        return value

    def validate_domain(self, value: str) -> str:
        if Domain.objects.filter(domain=value).exists():
            raise serializers.ValidationError("This domain is already registered.")
        return value

    def create(self, validated_data: dict) -> Tenant:
        domain = validated_data.pop("domain")
        email_domain = validated_data.pop("email_domain", "")
        tenant = Tenant.objects.create(**validated_data)
        Domain.objects.create(
            domain=domain,
            tenant=tenant,
            is_primary=True,
            email_domain=email_domain,
        )
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    """schema_name is excluded — immutable after creation."""

    class Meta:
        model = Tenant
        fields = ["name", "status", "logo_url", "primary_color"]
