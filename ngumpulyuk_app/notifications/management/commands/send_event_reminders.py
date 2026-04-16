from django.core.management.base import BaseCommand

from ngumpulyuk_app.notifications.notify import send_event_reminders_for_window


class Command(BaseCommand):
    help = (
        "Create in-app event_reminder notifications for participants whose event starts in ~24h. "
        "Run hourly via cron (e.g. 0 * * * *)."
    )

    def handle(self, *args, **options):
        n = send_event_reminders_for_window()
        self.stdout.write(self.style.SUCCESS(f"Created {n} reminder notification(s)."))
