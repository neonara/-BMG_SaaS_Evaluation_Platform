from django.contrib import admin
from .models import SocialAccount


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display  = ["user", "provider", "uid", "created_at", "updated_at"]
    list_filter   = ["provider"]
    search_fields = ["user__email", "uid"]
    readonly_fields = ["id", "uid", "provider", "extra_data", "created_at", "updated_at"]
