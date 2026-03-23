"""apps/users/tests/test_auth_views.py"""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestRegisterExternal:
    def test_registration_success(self, client):
        resp = client.post("/api/auth/register/", {
            "email": "new@gmail.com",
            "password": "Secure1234!",
            "password_confirm": "Secure1234!",
            "first_name": "Alice",
            "last_name": "Martin",
        }, format="json")
        assert resp.status_code == 201
        assert resp.data["email"] == "new@gmail.com"
        assert "password" not in resp.data

    def test_duplicate_email_returns_400(self, client):
        from apps.users.tests.factories import UserFactory
        UserFactory(email="dup@gmail.com")
        resp = client.post("/api/auth/register/", {
            "email": "dup@gmail.com",
            "password": "Secure1234!",
            "password_confirm": "Secure1234!",
            "first_name": "Bob",
            "last_name": "Dupont",
        }, format="json")
        assert resp.status_code == 400

    def test_password_mismatch_returns_400(self, client):
        resp = client.post("/api/auth/register/", {
            "email": "new2@gmail.com",
            "password": "Secure1234!",
            "password_confirm": "Different1234!",
            "first_name": "Alice",
            "last_name": "Martin",
        }, format="json")
        assert resp.status_code == 400

    def test_short_password_returns_400(self, client):
        resp = client.post("/api/auth/register/", {
            "email": "new3@gmail.com",
            "password": "short",
            "password_confirm": "short",
            "first_name": "A",
            "last_name": "B",
        }, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestPasswordReset:
    def test_always_returns_200(self, client):
        resp = client.post("/api/auth/password/reset/", {
            "email": "doesnotexist@test.com"
        }, format="json")
        # Always 200 — no email enumeration
        assert resp.status_code == 200

    def test_valid_email_sends_email(self, client, mailoutbox):
        from apps.users.tests.factories import UserFactory
        UserFactory(email="reset@test.com", status="active")
        resp = client.post("/api/auth/password/reset/", {
            "email": "reset@test.com"
        }, format="json")
        assert resp.status_code == 200

    def test_reset_confirm_invalid_token_returns_400(self, client):
        resp = client.post("/api/auth/password/reset/confirm/", {
            "token": "invalidtoken",
            "password": "NewSecure123!",
            "password_confirm": "NewSecure123!",
        }, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestOTPVerifyView:
    def test_valid_otp_activates_account(self, client):
        from apps.users.tests.factories import UserFactory
        from apps.users.otp import generate_and_store
        user = UserFactory(status="pending_otp")
        code = generate_and_store(user.email)
        resp = client.post("/api/auth/otp/verify/", {
            "email": user.email,
            "otp_code": code,
        }, format="json")
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data
        user.refresh_from_db()
        assert user.status == "active"

    def test_invalid_otp_returns_400(self, client):
        from apps.users.tests.factories import UserFactory
        from apps.users.otp import generate_and_store
        user = UserFactory(status="pending_otp")
        generate_and_store(user.email)
        resp = client.post("/api/auth/otp/verify/", {
            "email": user.email,
            "otp_code": "000000",
        }, format="json")
        assert resp.status_code == 400

    def test_invalid_otp_format_returns_400(self, client):
        resp = client.post("/api/auth/otp/verify/", {
            "email": "test@test.com",
            "otp_code": "abc",
        }, format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_without_auth_returns_401(self, client):
        resp = client.post("/api/auth/logout/", {"refresh": "token"})
        assert resp.status_code == 401

    def test_logout_blacklists_token(self, client):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(status="active")
        # Get token pair
        resp = client.post("/api/auth/token/", {
            "email": user.email,
            "password": "testpass123!",
        }, format="json")
        assert resp.status_code == 200
        refresh = resp.data["refresh"]
        # Logout
        client.force_authenticate(user=user)
        resp2 = client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        assert resp2.status_code == 204


@pytest.mark.django_db
class TestUserMeView:
    def test_unauthenticated_returns_401(self, client):
        assert client.get("/api/v1/users/me/").status_code == 401

    def test_get_own_profile(self, client):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(first_name="Alice", last_name="Martin", status="active")
        client.force_authenticate(user=user)
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code == 200
        assert resp.data["email"] == user.email
        assert resp.data["first_name"] == "Alice"

    def test_patch_own_profile(self, client):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(status="active")
        client.force_authenticate(user=user)
        resp = client.patch("/api/v1/users/me/", {
            "first_name": "Updated",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["first_name"] == "Updated"

    def test_cannot_change_role_via_me(self, client):
        from apps.users.tests.factories import UserFactory
        user = UserFactory(status="active")
        original_role = user.role
        client.force_authenticate(user=user)
        client.patch("/api/v1/users/me/", {"role": "super_admin"}, format="json")
        user.refresh_from_db()
        assert user.role == original_role


@pytest.mark.django_db
class TestUserDeactivateView:
    def test_deactivate_user(self, client):
        from apps.users.tests.factories import UserFactory
        from core.permissions.roles import Role
        hr = UserFactory(role=Role.HR, status="active")
        target = UserFactory(role=Role.INTERNAL_CANDIDATE, status="active")
        client.force_authenticate(user=hr)
        resp = client.post(f"/api/v1/users/{target.pk}/deactivate/", {
            "reason": "Employee has left the organisation."
        }, format="json")
        assert resp.status_code == 200
        target.refresh_from_db()
        assert target.status == "deactivated"

    def test_deactivate_already_deactivated_returns_400(self, client):
        from apps.users.tests.factories import UserFactory
        from core.permissions.roles import Role
        hr = UserFactory(role=Role.HR, status="active")
        target = UserFactory(status="deactivated")
        client.force_authenticate(user=hr)
        resp = client.post(f"/api/v1/users/{target.pk}/deactivate/", {
            "reason": "Already deactivated user"
        }, format="json")
        assert resp.status_code == 400

    def test_candidate_cannot_deactivate(self, client):
        from apps.users.tests.factories import UserFactory
        from core.permissions.roles import Role
        candidate = UserFactory(role=Role.EXTERNAL_CANDIDATE, status="active")
        target = UserFactory(status="active")
        client.force_authenticate(user=candidate)
        resp = client.post(f"/api/v1/users/{target.pk}/deactivate/", {
            "reason": "trying to deactivate"
        }, format="json")
        assert resp.status_code == 403
