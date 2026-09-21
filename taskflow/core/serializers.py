from datetime import date
from rest_framework import serializers
from .models import Project, Task, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = [
            "id", "project", "title", "description",
            "priority", "status", "due_date", "tags", "created_at", "source"
        ]

    def validate_due_date(self, value):
        if value and value < date.today():
            raise serializers.ValidationError("La fecha límite no puede ser en el pasado.")
        return value

    def validate(self, data):
        # Validación que involucra más de un campo
        if data.get("status") == "completada" and not data.get("due_date"):
            raise serializers.ValidationError(
                "No se puede marcar una tarea como completada sin fecha límite registrada."
            )
            
        # Validación Tarea Clase 4:
        # Una tarea no puede tener status="en_progreso" si su proyecto no tiene ninguna tarea completada todavía
        project = data.get("project")
        if not project and self.instance:
            project = self.instance.project
            
        status_val = data.get("status")
        if not status_val and self.instance:
            status_val = self.instance.status
            
        if status_val == "en_progreso" and project:
            if not project.tasks.filter(status="completada").exists():
                raise serializers.ValidationError(
                    "No se puede marcar una tarea en progreso si el proyecto no tiene tareas completadas."
                )

        return data


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "tasks", "created_at"]
