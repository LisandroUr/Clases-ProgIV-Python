from django.test import TestCase


class HealthCheckTest(TestCase):
    def test_health_check(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "TaskFlow API"}
        )

    def test_health_version(self):
        response = self.client.get("/api/health/version/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"version": "0.1.0"})

