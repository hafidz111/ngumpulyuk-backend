# Events are always free (no pricing) — product decision

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_event_is_free_price"),
    ]

    operations = [
        migrations.RemoveField(model_name="event", name="is_free"),
        migrations.RemoveField(model_name="event", name="price"),
    ]
