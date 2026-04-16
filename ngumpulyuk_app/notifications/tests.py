from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from ngumpulyuk_app.notifications import services
from ngumpulyuk_app.notifications.models import Notification
from ngumpulyuk_app.users.models import UserPreferences

User = get_user_model()


class NotificationServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="u1@test.com",
            full_name="User One",
            password="x",
            username="userone",
        )

    def test_skips_when_notification_disabled(self):
        UserPreferences.objects.create(
            user=self.user,
            notification_enabled=False,
        )
        n = services.create_notification(
            self.user,
            "community_post",
            title="t",
            message="m",
            related_id=None,
        )
        self.assertIsNone(n)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)

    def test_event_reminder_dedupe_exact_related(self):
        import uuid

        rid = uuid.uuid4()
        services.create_notification(
            self.user,
            "event_reminder",
            title="r",
            message="m",
            link_url="/events/x",
            related_id=rid,
            dedupe_exact_related=True,
        )
        again = services.create_notification(
            self.user,
            "event_reminder",
            title="r2",
            message="m2",
            link_url="/events/x",
            related_id=rid,
            dedupe_exact_related=True,
        )
        self.assertIsNone(again)
        self.assertEqual(
            Notification.objects.filter(user=self.user, type="event_reminder", related_id=rid).count(),
            1,
        )

    def test_dedup_window_for_event_update(self):
        import uuid

        rid = uuid.uuid4()
        services.create_notification(
            self.user,
            "event_update",
            title="t",
            message="m",
            related_id=rid,
            dedup_window_seconds=3600,
        )
        dup = services.create_notification(
            self.user,
            "event_update",
            title="t",
            message="m",
            related_id=rid,
            dedup_window_seconds=3600,
        )
        self.assertIsNone(dup)


class BlastNotificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            email="staff@test.com",
            full_name="Staff",
            password="x",
            username="staffuser",
        )
        self.staff.is_staff = True
        self.staff.save()
        self.member = User.objects.create_user(
            email="mem@test.com",
            full_name="Mem",
            password="x",
            username="memuser",
        )

    def test_blast_forbidden_for_non_staff(self):
        self.client.force_authenticate(user=self.member)
        r = self.client.post(
            "/api/v1/notifications/blast/",
            {
                "title": "Hi",
                "message": "Test",
                "user_ids": [str(self.member.id)],
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_blast_staff_targets_users(self):
        self.client.force_authenticate(user=self.staff)
        r = self.client.post(
            "/api/v1/notifications/blast/",
            {
                "title": "Pengumuman",
                "message": "Isi blast",
                "user_ids": [str(self.member.id)],
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["sent"], 1)
        self.assertEqual(
            Notification.objects.filter(user=self.member, type="admin_broadcast").count(),
            1,
        )
