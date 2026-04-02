"""
apps/multi_language/serializers.py
"""
from rest_framework import serializers
from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Language
        fields = ["code", "name", "is_active", "is_default", "flag_icon", "rtl"]
        read_only_fields = ["code"]


class LanguageAdminSerializer(serializers.ModelSerializer):
    """Used by Admin — allows activating/deactivating and setting default."""
    class Meta:
        model  = Language
        fields = ["code", "name", "is_active", "is_default", "flag_icon", "rtl"]

    def validate(self, attrs):
        # Only one language can be default
        if attrs.get("is_default"):
            Language.objects.filter(is_default=True).exclude(code=self.instance.code if self.instance else None).update(is_default=False)
        return attrs
