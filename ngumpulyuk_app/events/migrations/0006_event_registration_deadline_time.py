from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0005_event_registration_deadline"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="registration_deadline_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
