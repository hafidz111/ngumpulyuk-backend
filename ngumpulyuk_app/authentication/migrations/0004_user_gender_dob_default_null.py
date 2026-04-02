# Hanya isi gender & date_of_birth setelah onboarding; default null.

from django.db import migrations, models


def clear_dob_gender_if_not_onboarded(apps, schema_editor):
    User = apps.get_model("authentication", "User")
    User.objects.filter(onboarding_completed=False).update(
        gender=None,
        date_of_birth=None,
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_user_dob_optional_remove_event_pricing"),
    ]

    operations = [
        migrations.RunPython(clear_dob_gender_if_not_onboarded, noop_reverse),
        migrations.AlterField(
            model_name="user",
            name="date_of_birth",
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("male", "male"), ("female", "female"), ("other", "other")],
                default=None,
                max_length=20,
                null=True,
            ),
        ),
    ]
