"""apps/tenants/tests/test_models.py"""
import pytest


@pytest.mark.django_db
class TestTenantModel:
    def test_str_representation(self):
        from apps.tenants.tests.factories import TenantFactory
        tenant = TenantFactory.build(name="Acme", schema_name="acme")
        assert str(tenant) == "Acme (acme)"

    def test_default_status_is_trial(self):
        from apps.tenants.tests.factories import TenantFactory
        tenant = TenantFactory.build()
        assert tenant.status == "active"  # factory default

    def test_default_primary_color(self):
        from apps.tenants.tests.factories import TenantFactory
        tenant = TenantFactory.build()
        assert tenant.primary_color == "#1E3A8A"


@pytest.mark.django_db
class TestDomainModel:
    def test_get_tenant_by_email_domain_found(self):
        from apps.tenants.models import Domain
        from apps.tenants.tests.factories import DomainFactory, TenantFactory
        tenant = TenantFactory(schema_name="acme_corp_t")
        DomainFactory(tenant=tenant, email_domain="acme.com")
        result = Domain.get_tenant_by_email_domain("user@acme.com")
        assert result == tenant

    def test_get_tenant_by_email_domain_not_found(self):
        from apps.tenants.models import Domain
        result = Domain.get_tenant_by_email_domain("user@unknown.com")
        assert result is None

    def test_get_tenant_by_email_domain_invalid_email(self):
        from apps.tenants.models import Domain
        assert Domain.get_tenant_by_email_domain("notanemail") is None
        assert Domain.get_tenant_by_email_domain("") is None

    def test_str_representation(self):
        from apps.tenants.tests.factories import DomainFactory
        d = DomainFactory.build(domain="acme.bmg.tn")
        assert str(d) == "acme.bmg.tn"
