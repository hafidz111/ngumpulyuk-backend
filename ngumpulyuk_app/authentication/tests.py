from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class LastLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="lastlogin@test.com",
            full_name="Last Login User",
            password="secretpass123",
        )
        self.user.is_verified = True
        self.user.save(update_fields=["is_verified"])
        User.objects.filter(pk=self.user.pk).update(last_login=None)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.last_login)

    def test_email_login_sets_last_login(self):
        before = timezone.now()
        r = self.client.post(
            "/api/v1/auth/login/",
            {"email": "lastlogin@test.com", "password": "secretpass123"},
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)
        self.assertGreaterEqual(self.user.last_login, before)
