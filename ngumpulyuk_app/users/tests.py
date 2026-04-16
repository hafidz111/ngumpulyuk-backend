from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


User = get_user_model()


class AdminUserSearchTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(
            email="staff-search@test.com",
            full_name="Staff Search",
            password="x",
            username="staffsearch",
        )
        self.staff.is_staff = True
        self.staff.save()
        self.user = User.objects.create_user(
            email="fitri@mail.com",
            full_name="Fitri User",
            password="x",
            username="fitri",
        )

    def test_admin_can_search_user(self):
        self.client.force_authenticate(user=self.staff)
        r = self.client.get("/api/v1/users/?search=fitri")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["data"]["count"], 1)
        row = r.data["data"]["results"][0]
        self.assertEqual(row["email"], "fitri@mail.com")

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/v1/users/?search=fitri")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
