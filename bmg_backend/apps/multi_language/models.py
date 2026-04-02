"""Multi-language support models for the BMG backend.
This module defines the Language model, which represents a language that can be used in the application.
The Language model includes fields for the language code, name, active status, default status, flag icon, and right-to-left (RTL) text direction. This allows the application to support multiple languages and provide a way to manage them effectively.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Language(models.Model):
    code = models.CharField(max_length=10, primary_key=True)  # 'en', 'fr', 'es'
    name = models.CharField(max_length=100)  # 'English', 'Français'
    is_active = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    flag_icon = models.CharField(max_length=50, blank=True)
    rtl = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ["name"]
