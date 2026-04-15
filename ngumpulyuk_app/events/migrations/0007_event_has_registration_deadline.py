from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0006_event_registration_deadline_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="has_registration_deadline",
            field=models.BooleanField(default=False),
        ),
    ]
