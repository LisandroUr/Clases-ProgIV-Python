import csv
import json
import xml.etree.ElementTree as ET
import logging
from django.core.management.base import BaseCommand
from core.models import Task, Project

# Configuración de logging para la tarea
logging.basicConfig(
    filename='import.log',
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Importa tareas desde múltiples proveedores (JSON, CSV, XML)"

    def handle(self, *args, **options):
        """Punto de entrada del comando."""
        # Creamos proyecto por defecto porque ahora es obligatorio
        self.default_project, _ = Project.objects.get_or_create(
            name="Proyecto Importado",
            description="Proyecto por defecto para tareas importadas"
        )
        
        total = 0
        total += self._import_json("data/tasks_provider_a.json", source="proveedor_a")
        total += self._import_csv("data/tasks_provider_b.csv", source="proveedor_b")
        total += self._import_xml("data/tasks_provider_c.xml", source="proveedor_c")
        total += self._import_json("data/tasks_provider_d.json", source="proveedor_d")
        self.stdout.write(self.style.SUCCESS(f"Importación finalizada: {total} tareas cargadas"))

    def _import_json(self, path, source):
        """Carga tareas desde JSON."""
        count = 0
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if self._crear_task(item, source):
                    count += 1
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error importando {path}: {e}")
        return count

    def _import_csv(self, path, source):
        """Carga tareas desde CSV."""
        count = 0
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if self._crear_task(row, source):
                        count += 1
        except FileNotFoundError as e:
            logger.error(f"Error importando {path}: {e}")
        return count

    def _import_xml(self, path, source):
        """Carga tareas desde XML."""
        count = 0
        try:
            tree = ET.parse(path)
            for task_el in tree.getroot().findall("task"):
                item = {
                    "title": task_el.find("title").text if task_el.find("title") is not None else None,
                    "priority": task_el.find("priority").text if task_el.find("priority") is not None else "media",
                    "status": task_el.find("status").text if task_el.find("status") is not None else "pendiente",
                }
                if self._crear_task(item, source):
                    count += 1
        except (FileNotFoundError, ET.ParseError) as e:
            logger.error(f"Error importando {path}: {e}")
        return count

    def _crear_task(self, item, source):
        if not item.get("title"):
            logger.warning(f"Item sin título en {source}, se ignora")
            return False
        Task.objects.create(
            project=self.default_project,
            title=item["title"],
            priority=item.get("priority", "media"),
            status=item.get("status", "pendiente"),
            source=source,
        )
        return True
