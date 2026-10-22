from datetime import date
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from .models import Project, ProjectMembership, Task


class TaskFlowRBACPermissionTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin_proj", email="admin@ejemplo.com", password="claveSegura123!"
        )
        self.member_user = User.objects.create_user(
            username="miembro_proj", email="miembro@ejemplo.com", password="claveSegura123!"
        )
        self.stranger_user = User.objects.create_user(
            username="extrano", email="extrano@ejemplo.com", password="claveSegura123!"
        )

        self.project = Project.objects.create(name="Proyecto RBAC", description="Test")
        ProjectMembership.objects.create(
            project=self.project, user=self.admin_user, role="admin"
        )
        ProjectMembership.objects.create(
            project=self.project, user=self.member_user, role="miembro"
        )

    def test_admin_can_create_task(self):
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            "/api/tasks/",
            {
                "project": self.project.id,
                "title": "Tarea por admin",
                "due_date": str(date.today()),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_member_cannot_create_task(self):
        self.api_client.force_authenticate(user=self.member_user)
        response = self.api_client.post(
            "/api/tasks/",
            {
                "project": self.project.id,
                "title": "Tarea intento miembro",
                "due_date": str(date.today()),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_read_tasks(self):
        Task.objects.create(
            project=self.project,
            title="Tarea existente",
            status="pendiente",
            due_date=date.today(),
            owner=self.admin_user,
        )
        self.api_client.force_authenticate(user=self.member_user)
        response = self.api_client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_stranger_cannot_see_project(self):
        self.api_client.force_authenticate(user=self.stranger_user)
        response = self.api_client.get(f"/api/projects/{self.project.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_member_action_by_admin(self):
        self.api_client.force_authenticate(user=self.admin_user)
        response = self.api_client.post(
            f"/api/projects/{self.project.id}/add_member/",
            {"username": "extrano", "role": "miembro"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ProjectMembership.objects.filter(
                project=self.project, user=self.stranger_user
            ).exists()
        )
