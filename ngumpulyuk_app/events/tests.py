from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ngumpulyuk_app.events.models import Event

User = get_user_model()


class EventListUpcomingFilterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(
            email="creator@test.com",
            full_name="Creator",
            username="creator",
            password="x",
        )
        self.future = Event.objects.create(
            creator=self.creator,
            title="Future",
            description="d",
            category="Teknologi",
            event_date=date.today() + timedelta(days=3),
            event_time=time(10, 0),
            location_area="Jakarta",
            location_address="addr",
            max_participants=10,
            status="upcoming",
        )
        self.past_stale_status = Event.objects.create(
            creator=self.creator,
            title="Past stale",
            description="d",
            category="Teknologi",
            event_date=date.today() - timedelta(days=5),
            event_time=time(10, 0),
            location_area="Jakarta",
            location_address="addr",
            max_participants=10,
            status="upcoming",
        )

    def test_upcoming_list_excludes_past_dates_even_if_status_upcoming(self):
        r = self.client.get("/api/v1/events/?status=upcoming")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {e["id"] for e in r.data["data"]["events"]}
        self.assertIn(str(self.future.id), ids)
        self.assertNotIn(str(self.past_stale_status.id), ids)

    def test_past_list_includes_passed_dates(self):
        r = self.client.get("/api/v1/events/?status=past&sort=date_desc")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {e["id"] for e in r.data["data"]["events"]}
        self.assertNotIn(str(self.future.id), ids)
        self.assertIn(str(self.past_stale_status.id), ids)

    def test_list_payload_omits_description_for_lighter_response(self):
        r = self.client.get("/api/v1/events/?status=upcoming")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        events = r.data["data"]["events"]
        self.assertGreater(len(events), 0)
        self.assertNotIn("description", events[0])
        self.assertIn("title", events[0])
