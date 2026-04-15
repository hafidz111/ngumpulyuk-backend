from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0004_event_end_date_event_end_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="registration_deadline",
            field=models.DateField(blank=True, null=True),
        ),
    ]
