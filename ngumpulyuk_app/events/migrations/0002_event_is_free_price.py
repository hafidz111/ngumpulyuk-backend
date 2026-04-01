# Generated manually — align with database-schema.sql & API-documentation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="is_free",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="event",
            name="price",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
