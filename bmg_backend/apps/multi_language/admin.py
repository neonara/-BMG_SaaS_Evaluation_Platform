from django.contrib import admin
from .models import Language


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "is_active", "is_default", "rtl"]
    list_editable = ["is_active", "is_default"]
    ordering = ["name"]
