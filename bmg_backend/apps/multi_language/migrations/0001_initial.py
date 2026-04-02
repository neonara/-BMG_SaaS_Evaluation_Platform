from django.db import migrations, models


class Migration(migrations.Migration):
    initial      = True
    dependencies  = []
    operations   = [
        migrations.CreateModel(
            name="Language",
            fields=[
                ("code",       models.CharField(max_length=10, primary_key=True, serialize=False)),
                ("name",       models.CharField(max_length=100)),
                ("is_active",  models.BooleanField(default=False)),
                ("is_default", models.BooleanField(default=False)),
                ("flag_icon",  models.CharField(blank=True, max_length=50)),
                ("rtl",        models.BooleanField(default=False)),
            ],
            options={"ordering": ["name"], "db_table": "multi_language_language"},
        ),
    ]
