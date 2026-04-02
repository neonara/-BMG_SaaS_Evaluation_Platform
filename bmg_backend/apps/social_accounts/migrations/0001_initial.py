from django.conf import settings
import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial      = True
    dependencies  = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations   = [
        migrations.CreateModel(
            name="SocialAccount",
            fields=[
                ("id",               models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("provider",         models.CharField(choices=[("google","Google"),("linkedin","LinkedIn")], db_index=True, max_length=20)),
                ("uid",              models.CharField(db_index=True, max_length=255)),
                ("access_token",     models.TextField(blank=True)),
                ("refresh_token",    models.TextField(blank=True)),
                ("token_expires_at", models.DateTimeField(blank=True, null=True)),
                ("extra_data",       models.JSONField(default=dict)),
                ("created_at",       models.DateTimeField(auto_now_add=True)),
                ("updated_at",       models.DateTimeField(auto_now=True)),
                ("user",             models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="social_accounts", to=settings.AUTH_USER_MODEL)),
            ],
            options={"db_table": "social_accounts_socialaccount"},
        ),
        migrations.AlterUniqueTogether(name="socialaccount", unique_together={("provider","uid")}),
    ]
