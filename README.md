# Ziyu Jardinería — Sistema de Gestión de Visitas

Sistema web para gestionar solicitudes de visita de jardinería profesional.
Construido con Django 6.0.6 (MVT), PostgreSQL, Leaflet.js y JavaScript vanilla.

## Flujo del sistema

1. Un cliente solicita una visita a través del formulario público.
2. La empresa revisa las solicitudes en el panel interno (requiere autenticación).
3. Se asigna un jardinero (con validación de solapamiento de horarios).
4. El cliente recibe un enlace con token UUID único para confirmar o cancelar la visita.
5. El estado de la solicitud se actualiza en tiempo real.

## Requisitos previos

- Python 3.12+
- PostgreSQL 14+
- pip

## Instalación

```bash
# 1. Clonar el repositorio y entrar al directorio
cd backend-ziyu

# 2. Crear y activar el entorno virtual
python -m venv env

# Windows:
env\Scripts\activate

# Linux/Mac:
source env/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Editar el archivo .env con tus credenciales de PostgreSQL:
#   SECRET_KEY=tu-clave-secreta
#   DB_NAME=ziyu
#   DB_USER=postgres
#   DB_PASSWORD=tu-password
#   DB_HOST=localhost
#   DB_PORT=5432

# 5. Crear la base de datos en PostgreSQL
psql -U postgres -c "CREATE DATABASE ziyu;"

# 6. Ejecutar migraciones
python manage.py migrate

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Cargar datos iniciales (tipos de servicio y jardineros de ejemplo)
python manage.py load_initial_data

# 9. Iniciar el servidor de desarrollo
python manage.py runserver
```

Accede a `http://localhost:8000`

## Uso

### Formulario público de solicitud
- **URL:** `http://localhost:8000/`
- Cualquier persona puede solicitar una visita.
- Incluye mapa interactivo Leaflet — al hacer clic se actualizan automáticamente las coordenadas y la dirección (geocodificación inversa con Nominatim).
- Validación completa server-side con modal de errores.

### Panel de la empresa
- **URL:** `http://localhost:8000/panel/`
- Requiere autenticación (login de admin).
- Muestra estadísticas (cards), tabla de solicitudes con filtros por estado y servicio, y mapa con ubicaciones.
- Permite asignar jardineros con validación de solapamiento de horarios.

### Admin de Django
- **URL:** `http://localhost:8000/admin/`
- Gestión completa de todos los modelos.
- list_display, filtros, búsqueda, fieldsets y date_hierarchy configurados.

### Documentación del proyecto
- **URL:** `http://localhost:8000/documentacion/`
- Requiere autenticación.
- Muestra toda la documentación: comandos, funcionalidad, diagrama de BD, diagrama de procesos, rutas, seguridad, tests y estructura del proyecto.

### Confirmación de visita (cliente)
- **URL:** `http://localhost:8000/confirmar/<uuid>/`
- El cliente accede con su token único (previene IDOR) para confirmar o cancelar la visita.

## Operaciones con shell_plus

```bash
# Iniciar shell_plus (auto-importa todos los modelos)
python manage.py shell_plus
```

```python
# Ver todas las solicitudes
VisitRequest.objects.all()

# Filtrar por estado
VisitRequest.objects.filter(status='pendiente')

# Buscar por nombre de cliente
VisitRequest.objects.filter(client_name__icontains='María')

# Eliminar una solicitud específica por ID
solicitud = VisitRequest.objects.get(pk=1)
print(f"Eliminando: {solicitud}")
solicitud.delete()

# Eliminar todas las solicitudes canceladas
eliminadas, _ = VisitRequest.objects.filter(status='cancelada').delete()
print(f"Se eliminaron {eliminadas} solicitudes canceladas")

# Ver solicitudes de un jardinero específico
VisitRequest.objects.filter(gardener__first_name='Carlos')

# Verificar que se eliminó
VisitRequest.objects.filter(pk=1).exists()  # False
```

## Tests

```bash
python manage.py test visits -v 2
```

Los tests (~45) cubren:
- **Modelos:** creación, representación string, defaults, validación de horarios, solapamiento de jardineros
- **Formularios:** campos requeridos, validación de fechas pasadas, rangos horarios, servicios inactivos excluidos, coordenadas opcionales
- **Servicios:** disponibilidad de jardineros, detección de solapamiento, asignación exitosa/fallida
- **Vistas:** acceso público, acceso protegido con login, creación de solicitudes, dashboard con filtros, asignación
- **Seguridad:** IDOR con tokens falsos (404), login requerido (302), POST-only en asignación (405), confirmación por token

## Estructura del proyecto

```
backend-ziyu/
├── core/                          # Configuración Django
│   ├── settings/
│   │   ├── base.py                # Settings compartidos
│   │   ├── local.py               # Desarrollo (DEBUG, shell_plus)
│   │   └── prod.py                # Producción (HTTPS, HSTS)
│   ├── urls.py                    # URLs raíz
│   ├── wsgi.py
│   └── asgi.py
├── visits/                        # App principal
│   ├── management/commands/
│   │   └── load_initial_data.py   # Datos iniciales
│   ├── models.py                  # ServiceType, Gardener, VisitRequest
│   ├── views.py                   # 8 vistas (públicas + protegidas)
│   ├── forms.py                   # VisitRequestForm, AssignGardenerForm
│   ├── services.py                # Lógica de negocio (solapamiento)
│   ├── urls.py                    # 8 rutas con app_name
│   ├── admin.py                   # Admin personalizado
│   └── tests.py                   # ~45 tests
├── templates/
│   ├── base.html                  # Layout base
│   └── visits/
│       ├── visit_request_form.html
│       ├── visit_request_success.html
│       ├── company_dashboard.html
│       ├── visit_confirm.html
│       └── documentation.html
├── static/
│   ├── css/styles.css             # Design system completo
│   └── js/
│       ├── main.js                # Nav, alerts, modal de errores
│       └── map.js                 # Leaflet + geocodificación inversa
├── manage.py
├── requirements.txt
├── .env                           # Variables de entorno (NO en Git)
├── .gitignore
└── README.md
```

## Seguridad

- **CSRF:** protección en todos los formularios POST con `{% csrf_token %}`
- **IDOR:** URLs de confirmación usan UUID tokens, no PKs secuenciales
- **XSS:** auto-escaping de Django en templates, `escapeHtml()` en JS
- **Login:** panel de empresa y documentación protegidos con `@login_required`
- **POST-only:** asignación y logout requieren método POST (`@require_POST`)
- **Validación:** formularios con validación estricta server-side
- **SQL injection:** uso exclusivo del ORM de Django, sin queries crudas
- **Logout seguro:** mediante POST (compatible con Django 5+/6+)
