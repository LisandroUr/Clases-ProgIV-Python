from datetime import date, timedelta
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from .models import Project, Task


class TaskFlowAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name="Proyecto Demo", description="Descripción del proyecto"
        )

    def test_health_check(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "TaskFlow API"})

    def test_create_project(self):
        response = self.client.post(
            "/api/projects/",
            {"name": "Nuevo Proyecto", "description": "Detalles"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["name"], "Nuevo Proyecto")

    def test_due_date_in_past_fails(self):
        past_date = date.today() - timedelta(days=2)
        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project.id,
                "title": "Tarea con fecha pasada",
                "due_date": str(past_date),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()["error"])

    def test_en_progreso_without_completed_task_fails(self):
        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project.id,
                "title": "Tarea en progreso",
                "status": "en_progreso",
                "due_date": str(date.today() + timedelta(days=5)),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.json()["error"])

    def test_en_progreso_with_completed_task_succeeds(self):
        Task.objects.create(
            project=self.project,
            title="Tarea previa completada",
            status="completada",
            due_date=date.today(),
        )

        response = self.client.post(
            "/api/tasks/",
            {
                "project": self.project.id,
                "title": "Tarea en progreso permitida",
                "status": "en_progreso",
                "due_date": str(date.today() + timedelta(days=5)),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
