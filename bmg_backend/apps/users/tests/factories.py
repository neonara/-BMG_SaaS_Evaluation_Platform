"""apps/users/tests/factories.py"""
import factory
from factory.django import DjangoModelFactory

from apps.users.models import User
from core.permissions.roles import Role


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    role = Role.INTERNAL_CANDIDATE
    status = "active"
    password = factory.django.Password("testpass123!")

    class Params:
        super_admin = factory.Trait(
            role=Role.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
            email=factory.Sequence(lambda n: f"superadmin{n}@bmg.tn"),
        )
        admin_client = factory.Trait(
            role=Role.ADMIN_CLIENT,
            email=factory.Sequence(lambda n: f"adminclient{n}@org.com"),
        )
        hr = factory.Trait(
            role=Role.HR,
            email=factory.Sequence(lambda n: f"hr{n}@org.com"),
        )
        manager = factory.Trait(
            role=Role.MANAGER,
            email=factory.Sequence(lambda n: f"manager{n}@org.com"),
        )
        external = factory.Trait(
            role=Role.EXTERNAL_CANDIDATE,
            email=factory.Sequence(lambda n: f"ext{n}@gmail.com"),
        )
        pending_otp = factory.Trait(
            status="pending_otp",
            role=Role.INTERNAL_CANDIDATE,
        )
        deactivated = factory.Trait(
            status="deactivated",
        )
