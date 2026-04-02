"""
Migration: add preferred_language FK to User.
Depends on multi_language.0001_initial being run first.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users",          "0001_initial"),
        ("multi_language", "0001_initial"),
    ]
    operations = [
        migrations.AddField(
            model_name="user",
            name="preferred_language",
            field=models.ForeignKey(
                blank=True,
                null=True,
                db_column="preferred_language_code",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="users",
                to="multi_language.language",
            ),
        ),
    ]
