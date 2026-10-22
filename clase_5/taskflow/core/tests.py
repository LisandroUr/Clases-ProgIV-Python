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

    def test_complete_action_marks_completed(self):
        task = Task.objects.create(
            project=self.project,
            title="Tarea a completar",
            status="pendiente",
            due_date=date.today() + timedelta(days=2),
        )
        response = self.client.post(f"/api/tasks/{task.id}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "completada")

    def test_overdue_action_lists_expired_tasks(self):
        past_date = date.today() - timedelta(days=3)
        task = Task.objects.create(
            project=self.project,
            title="Tarea vencida",
            status="pendiente",
            due_date=past_date,
        )
        response = self.client.get("/api/tasks/overdue/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json().get("results", response.json())
        self.assertTrue(any(t["id"] == task.id for t in results))

    def test_project_summary_action(self):
        Task.objects.create(
            project=self.project,
            title="Tarea 1",
            status="pendiente",
            due_date=date.today(),
        )
        response = self.client.get(f"/api/projects/{self.project.id}/summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["pendiente"], 1)
