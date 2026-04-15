from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0007_event_has_registration_deadline"),
        ("discussions", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="thread",
            name="community",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="threads",
                to="communities.community",
            ),
        ),
        migrations.AddField(
            model_name="thread",
            name="related_event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="threads",
                to="events.event",
            ),
        ),
    ]
