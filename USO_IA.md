# Uso de Inteligencia Artificial — Prueba Técnica Ziyu Jardinería

## Herramienta utilizada

**Claude Code** (CLI de Anthropic, modelo Claude Sonnet 4.6), usado como un **sistema de agentes especializados** configurado con instrucciones personalizadas.

No es un chat genérico. Es un agente de desarrollo que opera directamente sobre el código del proyecto con acceso al sistema de archivos, terminal, git y herramientas de búsqueda. Puede leer, crear, editar archivos y ejecutar comandos.

## Agentes configurados

El sistema tiene agentes especializados que se invocan según el tipo de tarea:

| Agente | Rol | Cuándo se usa |
|---|---|---|
| `django-senior-dev` | Desarrollador Django senior (MVT) | Modelos, vistas, templates, forms, admin, SCSS, JS, tests, GeoDjango |
| `backend-architect-django` | Arquitecto backend Django/DRF | Diseño de APIs, PostgreSQL, seguridad, rendimiento |
| `senior-react-frontend-dev` | Desarrollador React senior | Componentes React, Tailwind, testing frontend |

Para este proyecto se usó principalmente `django-senior-dev` porque es una aplicación Django tradicional MVT sin REST Framework ni React.

## Instrucciones del agente

Cuando el agente recibe una instrucción, opera bajo estas reglas configuradas:

- Trabaja directamente sobre los archivos del proyecto (no genera respuestas genéricas, sino código aplicado).
- Antes de editar, lee el estado actual de los archivos para entender el contexto.
- Aplica seguridad por defecto: CSRF, validación server-side, protección contra IDOR, XSS, SQL injection.
- Sigue convenciones de Django: naming, estructura de apps, separación de responsabilidades.
- No agrega complejidad innecesaria ni abstrae prematuramente.
- Puede ejecutar comandos del sistema: `manage.py check`, `manage.py test`, `manage.py runserver`.
- Puede verificar el resultado de sus cambios lanzando el servidor y probando con curl.

---

## Registro de uso

Formato: **Prompt usado** → **Para qué lo usé** → **Qué hice con el resultado**

---

### 1. Análisis del proyecto

**Prompt:** "Analiza el proyecto dentro de la carpeta backend-ziyu que está la estructura base hecha en Django"
→ Para entender el estado actual del proyecto antes de empezar a construir.
→ El agente `django-senior-dev` exploró toda la estructura, leyó cada archivo (settings, urls, manage.py, .env, requirements.txt) y generó un informe completo con fortalezas, debilidades, problemas de seguridad y recomendaciones. Con eso supe qué tenía y qué faltaba.

---

### 2. Corrección de problemas críticos

**Prompt:** "Corrige todos los problemas críticos que encontraste"
→ Para resolver los problemas de seguridad y configuración antes de empezar a desarrollar.
→ El agente ejecutó las correcciones directamente:
- Eliminó `core/settings.py` (tenía la SECRET_KEY hardcodeada en texto plano).
- Creó `.gitignore` para proteger `.env`, `env/`, `__pycache__/`.
- Generó una SECRET_KEY segura y actualizó `.env`.
- Recodificó `requirements.txt` de UTF-16 LE a UTF-8.
- Agregó configuraciones de seguridad HTTPS/HSTS a `prod.py`.
- Corrigió el parsing de `ALLOWED_HOSTS` que podía generar `['']`.

---

### 3. Definición de requerimientos

**Prompt:** (El agente preguntó qué tipo de sistema era) → Le proporcioné todos los requerimientos funcionales completos: flujo de negocio, modelos, vistas, formularios, admin, mapa, estados, validaciones, diseño, tests, y estructura sugerida.
→ Para que el agente tuviera contexto completo antes de escribir una sola línea de código.
→ El agente usó estos requerimientos como especificación para construir toda la aplicación.

---

### 4. Construcción de la aplicación completa

**Prompt:** "Ahora crea la estructura base de las apps del proyecto" (con todos los requerimientos detallados)
→ Para construir el sistema completo de gestión de visitas.
→ El agente `django-senior-dev` creó ~20 archivos:
- **Modelos:** `ServiceType`, `Gardener`, `VisitRequest` con validación de solapamiento de horarios.
- **Forms:** `VisitRequestForm` con widgets personalizados, `AssignGardenerForm`.
- **Vistas:** 6 vistas (formulario público, éxito, dashboard protegido, asignación POST-only, confirmación y cancelación por token UUID).
- **URLs:** 6 rutas con `app_name`.
- **Admin:** Configuración completa con list_display, filtros, fieldsets, date_hierarchy.
- **Services:** Lógica de negocio separada (verificación de disponibilidad, asignación).
- **Tests:** 45 tests cubriendo modelos, forms, vistas, servicios y seguridad.
- **Templates:** base.html, formulario, éxito, dashboard con modal, confirmación.
- **Static:** CSS design system (~1200 líneas), main.js, map.js con Leaflet.
- **Management command:** Datos iniciales (5 servicios, 3 jardineros).
- Verificó con `manage.py check` (0 issues) y `manage.py test` (45/45 OK).

---

### 5. Correcciones post-testing

**Prompt:** "Estoy probando y falta el tema del logout ya que me sale 405, y cuando selecciono la dirección por el mapa no se actualiza el input de la dirección, y lo otro cuando haya algún error en los inputs también mandar un modal para indicarle cuál es el error... y aparte hazme una vista protegida para mostrar toda la documentación del proyecto incluyendo diagramas de base de datos y de procesos"
→ Para arreglar bugs que encontré probando en el navegador y agregar la vista de documentación.
→ El agente hizo 4 correcciones y 1 feature nueva:
- **Logout 405:** Django 6 requiere POST para logout. Cambió el link por un formulario POST con `@require_POST` + `auth_logout()`.
- **Mapa → dirección:** Agregó geocodificación inversa con Nominatim en `map.js`. Al hacer clic en el mapa ahora se actualiza automáticamente el campo de dirección.
- **Modal de errores:** Agregó un modal en el formulario que se muestra automáticamente cuando hay errores de validación, listando cada campo con su error.
- **Vista de documentación:** Creó `/documentacion/` protegida con `@login_required`, con 10 secciones: descripción, instalación paso a paso, funcionalidad, diagrama de BD (entidad-relación ASCII), diagrama de procesos (flujo de negocio + máquina de estados), tabla de endpoints, seguridad, shell_plus, tests, y estructura del proyecto.
- Actualizó el README.md con toda la información.

---

### 6. Verificación automatizada

**Prompt:** "Ahora prueba el servidor y verifica que todo funcione bien"
→ Para verificar que todo funciona en ejecución real, no solo en teoría.
→ El agente levantó el servidor con `runserver`, y probó cada feature con curl contra `localhost:8000`:
- Formulario público (200, con mapa y CSRF).
- Envío de solicitud (302 → éxito, registro creado en BD).
- Dashboard protegido (302 sin auth, 200 con auth, stats correctas).
- Documentación (encontró un TemplateSyntaxError y lo corrigió).
- Logout POST (funciona, sesión terminada).
- Validación de errores (9 campos con error, modal presente).
- Confirmación por token (200, cambia estado a confirmada).
- Probes de seguridad: IDOR con token falso (404), GET en POST-only (405), fecha pasada (error correcto), horario invertido (error correcto), cancelación (funciona).

---

### 7. Corrección del error encontrado en verificación

**Prompt:** "Arregla el error del template de documentación que encontró la verificación"
→ Para confirmar que el fix ya estaba aplicado.
→ El error era que `{% csrf_token %}` dentro del HTML de documentación se interpretaba como un tag de Django. Ya se había corregido durante la verificación usando `{% templatetag openblock %}`.


---

## Resumen

| # | Qué pedí | Resultado |
|---|---|---|
| 1 | Analizar el proyecto existente | Informe completo con problemas y recomendaciones |
| 2 | Corregir problemas críticos | 6 correcciones de seguridad y configuración |
| 3 | Definir requerimientos | Especificación completa del sistema |
| 4 | Construir la aplicación | ~20 archivos, 45 tests, app funcional completa |
| 5 | Arreglar bugs + vista de documentación | 4 fixes + página de documentación con diagramas |
| 6 | Verificar que todo funciona | Servidor probado con 17 checks, 1 bug encontrado y corregido |
| 7 | Confirmar fix de verificación | Ya estaba aplicado |


Cada interacción fue una instrucción concreta. Yo definí los requerimientos, probé el resultado en el navegador, reporté los bugs que encontré, y el agente los corrigió. El flujo fue: yo decido qué construir → el agente lo implementa → yo verifico → si hay problemas, los reporto → el agente los arregla.
