"""apps/tenants/tests/factories.py"""
import factory

from apps.tenants.models import Domain, Tenant


class TenantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Sequence(lambda n: f"Organisation {n}")
    schema_name = factory.Sequence(lambda n: f"org_{n}")
    status = "active"
    primary_color = "#1E3A8A"


class DomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Domain

    tenant = factory.SubFactory(TenantFactory)
    domain = factory.Sequence(lambda n: f"org{n}.bmg.tn")
    email_domain = factory.Sequence(lambda n: f"org{n}.com")
    is_primary = True
