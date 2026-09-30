from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Project, Task


class TaskFlowAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name="Proyecto de Prueba",
            description="Descripción de prueba"
        )
        self.future_date = (date.today() + timedelta(days=7)).isoformat()
        self.past_date = (date.today() - timedelta(days=7)).isoformat()

    def test_health_check(self):
        """El endpoint health_check debe responder 200 y status ok."""
        response = self.client.get("/api/health/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "TaskFlow API"})

    def test_cannot_create_task_with_past_due_date(self):
        """validate_due_date debe rechazar fechas límite en el pasado."""
        payload = {
            "project": self.project.id,
            "title": "Tarea fecha pasada",
            "due_date": self.past_date
        }
        response = self.client.post("/api/tasks/", payload, format="json", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue(data.get("error"))
        self.assertIn("La fecha límite no puede ser en el pasado.", str(data.get("detail")))

    def test_cannot_complete_task_without_due_date(self):
        """Una tarea no puede marcarse como completada sin due_date."""
        payload = {
            "project": self.project.id,
            "title": "Tarea sin fecha",
            "status": "completada"
        }
        response = self.client.post("/api/tasks/", payload, format="json", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue(data.get("error"))
        self.assertIn("No se puede marcar una tarea como completada sin fecha límite registrada.", str(data.get("detail")))

    def test_cannot_set_en_progreso_without_completed_task_in_project(self):
        """No se puede pasar a 'en_progreso' si el proyecto no tiene tareas completadas."""
        payload = {
            "project": self.project.id,
            "title": "Tarea en progreso",
            "status": "en_progreso"
        }
        response = self.client.post("/api/tasks/", payload, format="json", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue(data.get("error"))
        self.assertIn("No se puede pasar a 'en_progreso'", str(data.get("detail")))

    def test_patch_completada_with_existing_due_date(self):
        """En PATCH a 'completada', due_date se toma de self.instance si no viene en data."""
        task = Task.objects.create(
            project=self.project,
            title="Tarea existente con fecha",
            due_date=date.today() + timedelta(days=3),
            status="pendiente"
        )
        response = self.client.patch(
            f"/api/tasks/{task.id}/",
            {"status": "completada"},
            format="json",
            HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "completada")

    def test_can_set_en_progreso_when_project_has_completed_task(self):
        """Si el proyecto ya tiene al menos una tarea completada, se permite 'en_progreso'."""
        Task.objects.create(
            project=self.project,
            title="Tarea ya completada",
            due_date=date.today() + timedelta(days=2),
            status="completada"
        )
        payload = {
            "project": self.project.id,
            "title": "Segunda tarea en progreso",
            "status": "en_progreso"
        }
        response = self.client.post("/api/tasks/", payload, format="json", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
