from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from .models import Project, Task


class TaskFlowAuthTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.user1 = User.objects.create_user(
            username="ana", email="ana@ejemplo.com", password="claveSegura123!"
        )
        self.user2 = User.objects.create_user(
            username="beto", email="beto@ejemplo.com", password="claveSegura123!"
        )
        self.project = Project.objects.create(
            name="Proyecto Demo", description="Descripción del proyecto"
        )

    def test_health_check_public(self):
        response = self.api_client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "TaskFlow API"})

    def test_register_user(self):
        response = self.api_client.post(
            "/api/register/",
            {
                "username": "carlos",
                "email": "carlos@ejemplo.com",
                "password": "claveSegura123!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["username"], "carlos")
        self.assertNotIn("password", response.json())

    def test_obtain_jwt_token(self):
        response = self.api_client.post(
            "/api/token/",
            {"username": "ana", "password": "claveSegura123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.json())
        self.assertIn("refresh", response.json())

    def test_tasks_require_authentication(self):
        response = self.api_client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_sees_only_own_tasks(self):
        Task.objects.create(
            project=self.project,
            owner=self.user1,
            title="Tarea de Ana",
            status="pendiente",
            due_date=date.today(),
        )
        Task.objects.create(
            project=self.project,
            owner=self.user2,
            title="Tarea de Beto",
            status="pendiente",
            due_date=date.today(),
        )

        self.api_client.force_authenticate(user=self.user1)
        response = self.api_client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Tarea de Ana")
