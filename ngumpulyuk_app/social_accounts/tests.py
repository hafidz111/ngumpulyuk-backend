from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    GOOGLE_CLIENT_ID="test-client.apps.googleusercontent.com",
)
class GoogleSignInApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.google_profile = {
            "iss": "https://accounts.google.com",
            "aud": settings.GOOGLE_CLIENT_ID,
            "sub": "google-sub-123",
            "email": "google.user@example.com",
            "given_name": "Google",
            "family_name": "User",
        }

    @patch("ngumpulyuk_app.social_accounts.utils.Google.validate")
    def test_google_sign_in_creates_user_and_returns_tokens(self, mock_validate):
        mock_validate.return_value = self.google_profile
        r = self.client.post(
            "/api/v1/auth/google/",
            {"access_token": "fake-jwt-token"},
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["success"])
        payload = r.data["data"]
        self.assertIn("access_token", payload)
        self.assertIn("refresh_token", payload)
        user = User.objects.get(email="google.user@example.com")
        self.assertEqual(user.auth_provider, "google")
        self.assertTrue(user.is_verified)
        self.assertIsNotNone(user.last_login)

    @patch("ngumpulyuk_app.social_accounts.utils.Google.validate")
    def test_google_sign_in_existing_google_user(self, mock_validate):
        User.objects.create_user(
            email="google.user@example.com",
            full_name="Google User",
            password=settings.SOCIAL_AUTH_PASSWORD,
            auth_provider="google",
            is_verified=True,
        )
        mock_validate.return_value = self.google_profile
        r = self.client.post(
            "/api/v1/auth/google/",
            {"access_token": "fake-jwt-token"},
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertTrue(r.data["data"]["access_token"])

    @patch("ngumpulyuk_app.social_accounts.utils.Google.validate")
    def test_google_sign_in_links_unverified_email_account(self, mock_validate):
        User.objects.create_user(
            email="google.user@example.com",
            full_name="Email User",
            password="other-pass-123",
            is_verified=False,
        )
        mock_validate.return_value = self.google_profile
        r = self.client.post(
            "/api/v1/auth/google/",
            {"access_token": "fake-jwt-token"},
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        user = User.objects.get(email="google.user@example.com")
        self.assertEqual(user.auth_provider, "google")
        self.assertTrue(user.is_verified)

    @patch("ngumpulyuk_app.social_accounts.utils.Google.validate")
    def test_google_sign_in_rejects_verified_email_account(self, mock_validate):
        User.objects.create_user(
            email="google.user@example.com",
            full_name="Email User",
            password="other-pass-123",
            is_verified=True,
        )
        mock_validate.return_value = self.google_profile
        r = self.client.post(
            "/api/v1/auth/google/",
            {"access_token": "fake-jwt-token"},
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
