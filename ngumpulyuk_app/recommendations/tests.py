from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from ngumpulyuk_app.events.models import Event
from ngumpulyuk_app.recommendations.models import RecommendationSignal
from ngumpulyuk_app.users.models import UserInterest, UserPreferences

User = get_user_model()


class RecommendationFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="u@test.com",
            full_name="User",
            username="u",
            password="x",
        )
        self.creator = User.objects.create_user(
            email="creator@test.com",
            full_name="Creator",
            username="creator",
            password="x",
        )
        UserInterest.objects.create(user=self.user, interest_name="Teknologi")
        UserPreferences.objects.create(
            user=self.user,
            preferred_time="evening",
            preferred_location="Jakarta",
        )
        self.event = Event.objects.create(
            creator=self.creator,
            title="Tech Meetup",
            description="Event test",
            category="Teknologi",
            event_date=date.today() + timedelta(days=2),
            event_time=time(18, 30),
            location_area="Jakarta Selatan",
            location_address="Somewhere",
            max_participants=50,
            status="upcoming",
        )
        self.client.force_authenticate(user=self.user)

    def test_record_signal(self):
        r = self.client.post(
            "/api/v1/recommendations/signals/",
            {
                "event_id": str(self.event.id),
                "signal_type": "view",
                "dwell_ms": 22000,
                "platform": "web",
                "source": "event_detail",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(
            RecommendationSignal.objects.filter(
                user=self.user, event=self.event, signal_type="view"
            ).exists()
        )

    def test_recommendations_endpoint(self):
        RecommendationSignal.objects.create(
            user=self.user,
            event=self.event,
            signal_type="like",
            value=1,
            created_at=timezone.now(),
        )
        r = self.client.get("/api/v1/recommendations/events/?limit=5")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["success"])
        self.assertGreaterEqual(len(r.data["data"]["recommendations"]), 1)

    def test_recommendations_exclude_past_dates_with_stale_upcoming_status(self):
        Event.objects.create(
            creator=self.creator,
            title="Old Meetup",
            description="past",
            category="Teknologi",
            event_date=date.today() - timedelta(days=10),
            event_time=time(18, 30),
            location_area="Jakarta Selatan",
            location_address="Somewhere",
            max_participants=50,
            status="upcoming",
        )
        r = self.client.get("/api/v1/recommendations/events/?limit=10")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        ids = {item["event"]["id"] for item in r.data["data"]["recommendations"]}
        self.assertIn(str(self.event.id), ids)
        self.assertEqual(len(ids), 1)
