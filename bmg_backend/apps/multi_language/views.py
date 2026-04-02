"""
apps/multi_language/views.py

Public: list active languages
Admin:  full CRUD + set default
"""
from __future__ import annotations

from django.utils import translation
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Language
from .serializers import LanguageAdminSerializer, LanguageSerializer


class LanguageListView(APIView):
    """
    GET /api/v1/languages/         — returns active languages (public)
    POST /api/v1/languages/        — creates a new language (admin only)
    """
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request: Request) -> Response:
        langs = Language.objects.filter(is_active=True).order_by("name")
        return Response(LanguageSerializer(langs, many=True).data)

    def post(self, request: Request) -> Response:
        s = LanguageAdminSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class LanguageDetailView(APIView):
    """
    GET/PUT/PATCH/DELETE /api/v1/languages/{code}/  (admin only except GET)
    """
    def _get_object(self, code: str) -> Language | None:
        try:
            return Language.objects.get(code=code)
        except Language.DoesNotExist:
            return None

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request: Request, code: str) -> Response:
        lang = self._get_object(code)
        if not lang:
            return Response({"error": "Language not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(LanguageSerializer(lang).data)

    def patch(self, request: Request, code: str) -> Response:
        lang = self._get_object(code)
        if not lang:
            return Response({"error": "Language not found."}, status=status.HTTP_404_NOT_FOUND)
        s = LanguageAdminSerializer(lang, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, code: str) -> Response:
        lang = self._get_object(code)
        if not lang:
            return Response({"error": "Language not found."}, status=status.HTTP_404_NOT_FOUND)
        if lang.is_default:
            return Response(
                {"error": "Cannot delete the default language."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lang.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultLanguageView(APIView):
    """
    POST /api/v1/languages/{code}/set-default/   (admin)
    Sets the given language as the platform default.
    """
    permission_classes = [IsAdminUser]

    def post(self, request: Request, code: str) -> Response:
        try:
            lang = Language.objects.get(code=code, is_active=True)
        except Language.DoesNotExist:
            return Response({"error": "Active language not found."}, status=status.HTTP_404_NOT_FOUND)
        Language.objects.filter(is_default=True).update(is_default=False)
        lang.is_default = True
        lang.save(update_fields=["is_default"])
        return Response(LanguageSerializer(lang).data)


class UserLanguagePreferenceView(APIView):
    """
    GET  /api/v1/languages/me/     — returns the current user's language preference
    PUT  /api/v1/languages/me/     — updates it
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        lang_code = getattr(request.user, "preferred_language_id", None)
        if not lang_code:
            lang = Language.objects.filter(is_default=True).first()
            lang_code = lang.code if lang else "en"
        return Response({"preferred_language": lang_code})

    def put(self, request: Request) -> Response:
        code = request.data.get("preferred_language", "")
        if not Language.objects.filter(code=code, is_active=True).exists():
            return Response(
                {"error": f"Language '{code}' is not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.preferred_language_id = code
        request.user.save(update_fields=["preferred_language_id"])
        translation.activate(code)
        return Response({"preferred_language": code})
