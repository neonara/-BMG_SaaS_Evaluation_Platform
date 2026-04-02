from django.db import migrations


def seed_languages(apps, schema_editor):
    Language = apps.get_model("multi_language", "Language")
    Language.objects.bulk_create([
        Language(code="en", name="English",  is_active=True,  is_default=True,  flag_icon="🇬🇧", rtl=False),
        Language(code="fr", name="Français", is_active=True,  is_default=False, flag_icon="🇫🇷", rtl=False),
        Language(code="ar", name="العربية",  is_active=True,  is_default=False, flag_icon="🇹🇳", rtl=True),
    ], ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies  = [("multi_language", "0001_initial")]
    operations   = [migrations.RunPython(seed_languages, migrations.RunPython.noop)]
