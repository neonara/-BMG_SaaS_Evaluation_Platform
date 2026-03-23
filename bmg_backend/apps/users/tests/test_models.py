"""apps/users/tests/test_models.py"""
import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestUserModel:
    def test_str_representation(self):
        from apps.users.tests.factories import UserFactory
        from core.permissions.roles import Role
        user = UserFactory.build(email="test@test.com", role=Role.HR)
        assert str(user) == "test@test.com (hr)"

    def test_full_name_property(self):
        from apps.users.tests.factories import UserFactory
        user = UserFactory.build(first_name="Alice", last_name="Martin")
        assert user.full_name == "Alice Martin"

    def test_full_name_strips_whitespace(self):
        from apps.users.tests.factories import UserFactory
        user = UserFactory.build(first_name="  Alice  ", last_name="Martin")
        assert user.full_name == "Alice   Martin"

    def test_deactivate_sets_status_and_timestamp(self):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(status="active")
        user.deactivate()
        user.refresh_from_db()
        assert user.status == "deactivated"
        assert user.deactivated_at is not None
        assert user.deactivated_at <= timezone.now()

    def test_reactivate_clears_deactivation(self):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(status="deactivated")
        user.deactivated_at = timezone.now()
        user.recovery_token = "tok"
        user.save()
        user.reactivate()
        user.refresh_from_db()
        assert user.status == "active"
        assert user.deactivated_at is None
        assert user.recovery_token == ""

    def test_create_user_defaults(self):
        from apps.users.models import User
        user = User.objects.create_user(
            email="newuser@test.com",
            password="pass123",
            first_name="A",
            last_name="B",
        )
        assert user.status == "active"
        assert user.is_staff is False
        assert user.check_password("pass123")

    def test_create_superuser(self):
        from apps.users.models import User
        sa = User.objects.create_superuser(
            email="sa@bmg.tn",
            password="admin123",
            first_name="Super",
            last_name="Admin",
        )
        assert sa.is_staff is True
        assert sa.is_superuser is True
        from core.permissions.roles import Role
        assert sa.role == Role.SUPER_ADMIN
