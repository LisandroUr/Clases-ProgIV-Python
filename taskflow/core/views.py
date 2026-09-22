from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


def health_check(request):
    """Endpoint básico para verificar que la API está viva."""
    return JsonResponse({"status": "ok", "service": "TaskFlow API"})

# Clase 1: Tarea para la casa
def health_check_version(request):
    """Devuelve la versión actual de la API."""
    return JsonResponse({"version": "0.1.0"})

# Clase 3: Tarea para la casa (Implementación manual con get_object_or_404)
@api_view(["GET"])
def project_detail(request, project_id):
    """Devuelve un único proyecto, implementado de forma manual."""
    project = get_object_or_404(Project, id=project_id)
    serializer = ProjectSerializer(project)
    return Response(serializer.data)


class ProjectViewSet(viewsets.ModelViewSet):
    """CRUD completo para los proyectos."""
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD completo para las tareas, optimizado con prefetch/select_related."""
    queryset = Task.objects.select_related("project").prefetch_related("tags").all()
    serializer_class = TaskSerializer
