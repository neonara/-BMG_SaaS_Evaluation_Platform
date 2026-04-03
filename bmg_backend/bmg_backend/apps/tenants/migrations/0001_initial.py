"""Initial migration for tenants app (public schema)."""
from __future__ import annotations
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("schema_name",   models.CharField(db_index=True, max_length=63, unique=True)),
                ("id",            models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name",          models.CharField(max_length=255)),
                ("logo_url",      models.URLField(blank=True)),
                ("primary_color", models.CharField(default="#1E3A8A", max_length=7)),
                ("status",        models.CharField(
                    choices=[
                        ("active",    "Active"),
                        ("suspended", "Suspended"),
                        ("trial",     "Trial"),
                    ],
                    default="trial", max_length=20,
                )),
                ("created_on", models.DateField(auto_now_add=True)),
            ],
            options={"db_table": "tenants_tenant"},
        ),
        migrations.CreateModel(
            name="Domain",
            fields=[
                ("id",           models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ("domain",       models.CharField(db_index=True, max_length=253, unique=True)),
                ("is_primary",   models.BooleanField(db_index=True, default=True)),
                ("email_domain", models.CharField(blank=True, db_index=True, max_length=255)),
                ("tenant",       models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="domains",
                    to="tenants.tenant",
                )),
            ],
            options={"db_table": "tenants_domain"},
        ),
    ]
