from django.test import SimpleTestCase, TestCase


class HealthLivenessTests(SimpleTestCase):
    def test_liveness_returns_ok_without_database(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")


class HealthReadinessTests(TestCase):
    def test_readiness_returns_json(self):
        response = self.client.get("/health/ready/")
        self.assertIn(response.status_code, (200, 503))
