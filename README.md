# Clases de Programación IV — Python / Django

Repositorio con el desarrollo progresivo de las clases prácticas de Programación IV:

## Estructura de Clases

- **`clase_1/`**: Configuración inicial de Django, variables de entorno con `python-dotenv` y endpoints de salud (`/api/health/`, `/api/health/version/`).
- **`clase_2/`**: Modelado ORM (`Task`), migraciones y comando de importación de datos multi-formato (`import_tasks`) con JSON, CSV, XML y logging de errores.
- **`clase_3/`**: Modelos relacionales (`Project`, `Tag`), Serializers anidados de DRF y vistas con `@api_view` optimizadas con `select_related`/`prefetch_related`.
- **`clase_4/`**: CRUD completo mediante `ModelViewSet`, Routers, manejador global de excepciones y validaciones de negocio en serializers.
- **`clase_5/`**: Arquitectura en capas (`repositories.py`, `services.py`), caché local, filtros avanzados con `django-filter`, paginación y consumo de API externa de feriados (`HolidayService`).
- **`clase_6/`**: Autenticación mediante JSON Web Tokens (JWT) con `djangorestframework-simplejwt`, registro de usuarios y control de acceso (defensa contra IDOR/BOLA).
- **`clase_7/`**: Control de acceso basado en roles (RBAC) con `ProjectMembership`, permisos personalizados (`IsProjectAdminOrReadOnly`), transacciones atómicas y autenticación federada OAuth 2.0 (Google Login).
- **`clase_8/`**: Seguridad integral de APIs: OWASP Top 10, rate limiting/throttling (`LoginRateThrottle`), políticas CORS (`django-cors-headers`), sanitización de entradas contra XSS (`nh3`) y auditoría con `SecurityLog`.
- **`clase_9/`**: Migración a ASGI con Daphne, tiempo real mediante WebSockets con Django Channels y suscripción a grupos por proyecto.

## Ejecución de Tests

Para ejecutar las pruebas en cualquiera de las carpetas:
```bash
python manage.py test core
```