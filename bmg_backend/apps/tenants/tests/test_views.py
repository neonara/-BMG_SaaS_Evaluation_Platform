"""apps/tenants/tests/test_views.py"""
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def super_admin(db):
    from apps.users.tests.factories import UserFactory
    from core.permissions.roles import Role
    return UserFactory(role=Role.SUPER_ADMIN, status="active")


@pytest.mark.django_db
class TestTenantListView:
    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.get("/api/v1/tenants/")
        assert resp.status_code == 401

    def test_super_admin_can_list(self, api_client, super_admin):
        api_client.force_authenticate(user=super_admin)
        resp = api_client.get("/api/v1/tenants/")
        assert resp.status_code == 200
        assert "results" in resp.data

    def test_non_super_admin_returns_403(self, api_client):
        from apps.users.tests.factories import UserFactory
        from core.permissions.roles import Role
        hr = UserFactory(role=Role.HR, status="active")
        api_client.force_authenticate(user=hr)
        resp = api_client.get("/api/v1/tenants/")
        assert resp.status_code == 403


@pytest.mark.django_db
class TestTenantCreateView:
    def test_create_tenant_success(self, api_client, super_admin):
        api_client.force_authenticate(user=super_admin)
        payload = {
            "name": "Test Corp",
            "schema_name": "test_corp_x",
            "domain": "testcorpx.bmg.tn",
            "email_domain": "testcorpx.com",
            "status": "trial",
        }
        resp = api_client.post("/api/v1/tenants/", payload, format="json")
        assert resp.status_code == 201
        assert resp.data["schema_name"] == "test_corp_x"
        assert resp.data["name"] == "Test Corp"

    def test_duplicate_schema_name_returns_400(self, api_client, super_admin):
        from apps.tenants.tests.factories import TenantFactory
        TenantFactory(schema_name="dup_corp")
        api_client.force_authenticate(user=super_admin)
        payload = {
            "name": "Dup Corp",
            "schema_name": "dup_corp",
            "domain": "dupcorp.bmg.tn",
        }
        resp = api_client.post("/api/v1/tenants/", payload, format="json")
        assert resp.status_code == 400

    def test_invalid_schema_name_format(self, api_client, super_admin):
        api_client.force_authenticate(user=super_admin)
        payload = {
            "name": "Bad Corp",
            "schema_name": "Bad Corp!",
            "domain": "bad.bmg.tn",
        }
        resp = api_client.post("/api/v1/tenants/", payload, format="json")
        assert resp.status_code == 400
