"""apps/tenants/views.py"""
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from apps.tenants.models import Tenant
from apps.tenants.serializers import (
    TenantCreateSerializer,
    TenantSerializer,
    TenantUpdateSerializer,
)
from core.permissions.permissions import IsSuperAdmin


class TenantViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Tenant CRUD — Super Admin BMG only.
    """

    permission_classes = [IsSuperAdmin]
    queryset = Tenant.objects.all().prefetch_related("domains")
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return TenantCreateSerializer
        if self.action in ("partial_update", "update"):
            return TenantUpdateSerializer
        return TenantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = serializer.save()
        return Response(
            TenantSerializer(tenant).data,
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
