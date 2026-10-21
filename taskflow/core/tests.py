from datetime import date, timedelta
from django.core.cache import cache
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

    def test_complete_action_success(self):
        """La acción POST /api/tasks/<id>/complete/ completa una tarea que tiene fecha límite."""
        task = Task.objects.create(
            project=self.project,
            title="Tarea a completar",
            due_date=date.today() + timedelta(days=2),
            status="pendiente",
        )
        response = self.client.post(f"/api/tasks/{task.id}/complete/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.status, "completada")

    def test_complete_action_fails_without_due_date(self):
        """La acción POST /api/tasks/<id>/complete/ rechaza completar una tarea sin fecha límite."""
        task = Task.objects.create(
            project=self.project,
            title="Tarea sin fecha límite",
            due_date=None,
            status="pendiente",
        )
        response = self.client.post(f"/api/tasks/{task.id}/complete/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertTrue(data.get("error"))
        self.assertIn("sin fecha límite registrada", str(data.get("detail")))

    def test_overdue_action(self):
        """GET /api/tasks/overdue/ devuelve únicamente tareas vencidas no completadas."""
        task_overdue = Task.objects.create(
            project=self.project,
            title="Tarea vencida",
            due_date=date.today() - timedelta(days=5),
            status="pendiente",
        )
        Task.objects.create(
            project=self.project,
            title="Tarea vencida pero completada",
            due_date=date.today() - timedelta(days=5),
            status="completada",
        )
        Task.objects.create(
            project=self.project,
            title="Tarea futura",
            due_date=date.today() + timedelta(days=5),
            status="pendiente",
        )
        response = self.client.get("/api/tasks/overdue/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        results = data.get("results", data)
        task_ids = [t["id"] for t in results]
        self.assertIn(task_overdue.id, task_ids)
        self.assertEqual(len(results), 1)

    def test_pagination_and_ordering(self):
        """Verifica paginación (5 por página) y ordenamiento."""
        for i in range(7):
            Task.objects.create(
                project=self.project,
                title=f"Tarea paginada {i}",
                due_date=date.today() + timedelta(days=i + 1),
                priority="media",
            )
        response = self.client.get("/api/tasks/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("next", data)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 5)

    def test_filtering_and_search(self):
        """Verifica filtros por status, priority y búsqueda por texto."""
        t1 = Task.objects.create(
            project=self.project,
            title="Buscar Wireframe",
            description="Crear diseño",
            priority="alta",
            status="pendiente",
        )
        t2 = Task.objects.create(
            project=self.project,
            title="Otra tarea",
            description="Sin coincidencias",
            priority="baja",
            status="pendiente",
        )
        # Filtro exacto por priority
        res_filter = self.client.get("/api/tasks/?priority=alta", HTTP_HOST="localhost")
        self.assertEqual(res_filter.status_code, status.HTTP_200_OK)
        ids = [t["id"] for t in res_filter.json()["results"]]
        self.assertIn(t1.id, ids)
        self.assertNotIn(t2.id, ids)

        # Búsqueda parcial por search
        res_search = self.client.get("/api/tasks/?search=Wireframe", HTTP_HOST="localhost")
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        search_ids = [t["id"] for t in res_search.json()["results"]]
        self.assertIn(t1.id, search_ids)
        self.assertNotIn(t2.id, search_ids)

    def test_due_on_holiday(self):
        """Verifica que el campo due_on_holiday se serialice correctamente."""
        year = date.today().year
        holiday_date = date(year, 12, 25)
        cache.set(f"holidays_{year}", [holiday_date.isoformat()], timeout=3600)

        task = Task.objects.create(
            project=self.project,
            title="Tarea en feriado",
            due_date=holiday_date,
            status="pendiente",
        )
        response = self.client.get(f"/api/tasks/{task.id}/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json().get("due_on_holiday"))

    def test_project_summary(self):
        """Verifica la acción GET /api/projects/<id>/summary/ (Tarea Clase 5)."""
        Task.objects.create(project=self.project, title="T1", status="pendiente")
        Task.objects.create(project=self.project, title="T2", status="pendiente")
        Task.objects.create(project=self.project, title="T3", status="en_progreso")
        Task.objects.create(
            project=self.project,
            title="T4",
            status="completada",
            due_date=date.today() + timedelta(days=1),
        )
        response = self.client.get(f"/api/projects/{self.project.id}/summary/", HTTP_HOST="localhost")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["pendiente"], 2)
        self.assertEqual(data["en_progreso"], 1)
        self.assertEqual(data["completada"], 1)
