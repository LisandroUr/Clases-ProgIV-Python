from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


def health_check(request):
    return JsonResponse({"status": "ok", "service": "TaskFlow API"})


@api_view(["GET"])
def project_list(request):
    projects = Project.objects.all()
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    serializer = ProjectSerializer(project)
    return Response(serializer.data)


@api_view(["GET"])
def task_list(request):
    tasks = Task.objects.select_related("project").prefetch_related("tags").all()
    serializer = TaskSerializer(tasks, many=True)
    return Response(serializer.data)
