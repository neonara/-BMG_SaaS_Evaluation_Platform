"""
conftest.py — root pytest configuration.
"""
import django
import pytest


# ── pytest-django settings ────────────────────────────────────────────────────
# The DJANGO_SETTINGS_MODULE is set in pytest.ini.
# These fixtures are available globally in all tests.


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear the cache before and after each test."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def super_admin(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(super_admin=True)


@pytest.fixture
def admin_client_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(admin_client=True)


@pytest.fixture
def hr_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(hr=True)


@pytest.fixture
def manager_user(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(manager=True)


@pytest.fixture
def internal_candidate(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(status="active")


@pytest.fixture
def external_candidate(db):
    from apps.users.tests.factories import UserFactory
    return UserFactory(external=True)


@pytest.fixture
def auth_client(api_client, internal_candidate):
    """APIClient pre-authenticated as an internal candidate."""
    api_client.force_authenticate(user=internal_candidate)
    return api_client


@pytest.fixture
def hr_auth_client(api_client, hr_user):
    """APIClient pre-authenticated as HR."""
    api_client.force_authenticate(user=hr_user)
    return api_client


@pytest.fixture
def sa_auth_client(api_client, super_admin):
    """APIClient pre-authenticated as Super Admin BMG."""
    api_client.force_authenticate(user=super_admin)
    return api_client
