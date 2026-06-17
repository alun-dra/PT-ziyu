# Respuestas — Prueba Tecnica Ziyu Jardineria

---

## A.1 Logica y resolución de problemas

### 1. Encontrar solicitudes duplicadas (mismo cliente y misma dirección)

Lo que haría es agrupar las solicitudes por la combinación de nombre del cliente y dirección, y después quedarme solo con los grupos que tengan más de un registro.

En pseudocódigo sería algo así:

```
agrupadas = {}

para cada solicitud en lista_solicitudes:
    clave = (solicitud.client_name.lower().strip(), solicitud.address.lower().strip())
    si clave no está en agrupadas:
        agrupadas[clave] = []
    agrupadas[clave].agregar(solicitud)

duplicadas = [grupo for grupo en agrupadas.values() si len(grupo) > 1]
```

En Django se puede hacer directo con el ORM:

```python
from django.db.models import Count

duplicadas = (
    VisitRequest.objects
    .values('client_name', 'address')
    .annotate(total=Count('id'))
    .filter(total__gt=1)
)
```

**Costo:** La versión con diccionario recorre la lista una sola vez, así que es O(n) en tiempo y O(n) en espacio. La versión SQL con `GROUP BY` también es eficiente porque la base de datos lo optimiza internamente, y si hay un índice compuesto en `(client_name, address)` es todavía más rápido.

Un detalle importante: habría que normalizar los datos antes de comparar (quitar espacios extra, poner todo en minúsculas), porque "Juan Pérez" y "juan  pérez" deberían considerarse el mismo cliente.

---

### 2. Diagnostico: cita confirmada sin jardinero asignado

Seguiría estos pasos:

1. **Reproducir el caso:** Primero intentaria encontrar un registro concreto en la base de datos donde `status = 'confirmada'` y `gardener IS NULL`. Si existe, ya tengo evidencia real del problema.

   ```python
   VisitRequest.objects.filter(status='confirmada', gardener__isnull=True)
   ```

2. **Revisar el flujo de estados:** El flujo normal es pendiente → asignada → confirmada. Para que una visita pase a "confirmada", primero tiene que estar "asignada" (que implica tener jardinero). Revisaría si hay algún camino alternativo donde se pueda confirmar sin pasar por la asignación, por ejemplo desde el admin de Django donde se puede editar el estado manualmente sin pasar por la validación del servicio.

3. **Revisar el admin:** En el `VisitRequestAdmin` tenemos `list_editable = ('status', 'gardener')`. Esto permite que alguien cambie el estado a "confirmada" directamente desde la lista del admin sin necesariamente asignar un jardinero. Esta es la causa más probable.

4. **Revisar condiciones de carrera:** Podria pasar que un administrador desasigne al jardinero (lo ponga en NULL) justo después de que el cliente confirme. Es poco probable pero posible si dos personas están editando la misma solicitud al mismo tiempo.

5. **Revisar los logs del servidor:** Si hay logging configurado, buscaría las peticiones POST al endpoint de confirmacion y al admin para ver el orden de las operaciones.

**Solución que aplicaría:** Agregaria una validación en el método `clean()` del modelo o un `pre_save` signal que impida que el estado sea "confirmada" si no hay jardinero asignado. También restringiria en el admin que transiciones de estado son validas.

---

### 3. Validación frontend vs backend

La **validación en el frontend** ocurre en el navegador del usuario, antes de que los datos se envien al servidor. Por ejemplo, marcar un campo como obligatorio con HTML5 (`required`) o verificar con JavaScript que el email tenga un formato valido. La ventaja es que es instantanea: el usuario ve el error al momento sin esperar una respuesta del servidor.

La **validación en el backend** ocurre en el servidor cuando ya se recibieron los datos. Verifica las mismas reglas y otras mas complejas que solo se pueden hacer ahi, como comprobar que no existan duplicados en la base de datos o que un jardinero no tenga horarios superpuestos.

**¿Por qué no basta con uno solo?**

- Si solo valido en el frontend, cualquier persona puede saltarse esa validacion. Basta con abrir las herramientas de desarrollador del navegador, desactivar el JavaScript, o enviar una petición directa con curl o Postman. El servidor recibiria datos basura o maliciosos sin ningún filtro. Esto es un riesgo de seguridad serio.

- Si solo valido en el backend, funciona y es seguro, pero la experiencia del usuario es mala. Tiene que esperar a que el formulario se envie al servidor, el servidor lo procese, y le devuelva la pagina con los errores. Es lento y frustrante.

Lo ideal es hacer las dos: el frontend para dar una experiencia rapida y fluida, y el backend como la barrera real de seguridad que nunca se puede saltar. El frontend es una cortesia, el backend es la ley.

---

## A.2 Técnicas (Django / Python / Web)

### 1. ForeignKey vs ManyToManyField

**ForeignKey** establece una relación de "muchos a uno". Un registro de la tabla hija apunta a un solo registro de la tabla padre.

Ejemplo en jardinería: Una solicitud de visita tiene **un** tipo de servicio. Muchas solicitudes pueden ser de "Poda de arboles", pero cada solicitud individual solo tiene un tipo de servicio asignado.

```python
class VisitRequest(models.Model):
    service_type = models.ForeignKey(ServiceType, on_delete=models.PROTECT)
```

**ManyToManyField** establece una relación de "muchos a muchos". Un registro puede estar asociado a varios de la otra tabla, y viceversa.

Ejemplo en jardinería: Imagina que un jardinero puede tener varias certificaciones (poda en altura, manejo de pesticidas, riego tecnificado), y cada certificación la pueden tener varios jardineros.

```python
class Certification(models.Model):
    name = models.CharField(max_length=100)

class Gardener(models.Model):
    certifications = models.ManyToManyField(Certification)
```

La diferencia práctica es que ForeignKey agrega una columna en la tabla (un ID que apunta a la otra tabla), mientras que ManyToManyField crea una tabla intermedia que relaciona ambas.

---

### 2. Migraciones en Django

Una migracion es un archivo Python que describe un cambio en la estructura de la base de datos: crear una tabla, agregar una columna, cambiar un tipo de dato, agregar un indice, etc.

El problema que resuelve es mantener sincronizados los modelos de Django (el código Python) con el esquema real de la base de datos. Sin migraciones, cada vez que modificas un modelo tendrias que escribir SQL a mano y ejecutarlo en cada entorno (desarrollo, staging, produccion), lo cual es propenso a errores y difícil de coordinar en equipo.

**¿Que pasa si modificas un modelo y no creas la migracion?**

Django va a seguir usando el esquema anterior de la base de datos. Si por ejemplo agregaste un campo nuevo al modelo, al intentar guardar un registro vas a recibir un error porque la columna no existe en la tabla real. El ORM intenta insertar datos en una columna que la base de datos no conoce, y falla.

Además, si otro desarrollador del equipo hace `git pull` y ejecuta `migrate`, no va a recibir tu cambio porque no hay archivo de migracion que aplicar. Su base de datos va a quedar desactualizada respecto al código.

---

### 3. Patron MTV (Model–Template–View)

Es la forma en que Django organiza el código de una aplicacion web. Cada parte tiene una responsabilidad clara:

- **Model (Modelo):** Se encarga de los datos. Define la estructura de las tablas en la base de datos, las relaciones entre ellas, y las reglas de validacoón del negocio. Por ejemplo, el modelo `VisitRequest` define que campos tiene una solicitud de visita y valida que no haya solapamiento de horarios.

- **Template (Plantilla):** Se encarga de la presentacion. Es el HTML que ve el usuario, con la lógica mínima necesaria para mostrar datos dinamicos (bucles, condicionales). Por ejemplo, `company_dashboard.html` muestra la tabla de solicitudes y las tarjetas de estadisticas.

- **View (Vista):** Se encarga de la logica de cada peticion. Recibe la petición HTTP del usuario, consulta o modifica los datos a traves del modelo, y decide que template renderizar con que datos. Por ejemplo, la vista `company_dashboard` filtra las solicitudes, calcula estadisticas, y pasa todo eso al template.

El flujo es: el usuario hace una petición → la **View** la recibe, consulta el **Model**, y renderiza un **Template** con los datos → el HTML resultante se envia al navegador.

---

### 4. requirements.txt y por que no subir el venv

**requirements.txt** es un archivo que lista todas las dependencias del proyecto con sus versiones exactas. Sirve para que cualquier persona pueda recrear el mismo entorno de ejecucion con un solo comando (`pip install -r requirements.txt`). Garantiza que todos trabajen con las mismas versiones de las librerías.

**¿Por que es mala práctica subir el entorno virtual al repositorio?**

- **Peso innecesario:** Un venv puede pesar cientos de megabytes. Son archivos binarios compilados para un sistema operativo especifico. Subirlos infla el repositorio sin razon, porque se pueden regenerar en segundos con `pip install`.

- **No es portable:** Los binarios compilados en Windows no funcionan en Linux y viceversa. Si un compañero trabaja en Mac y tú en Windows, tu venv no le sirve.

- **Ruido en el historial:** Cada actualización de una libreroa genera cientos de archivos modificados en el diff, lo que hace imposible revisar los cambios reales del código.

Lo correcto es agregar `env/` o `venv/` al `.gitignore` y mantener el `requirements.txt` actualizado. Así el repositorio queda liviano y portable.

---

### 5. Consulta a la BD dentro de un bucle (problema N+1)

Este es el clasico problema de las **N+1 queries**. Pasa cuando haces una consulta para traer una lista de registros (1 query), y después dentro del bucle haces otra consulta por cada registro para traer datos relacionados (N queries adicionales).

Ejemplo concreto:

```python
# MAL: 1 query para las visitas + 1 query por cada visita para traer el jardinero
visitas = VisitRequest.objects.all()  # 1 query
for visita in visitas:
    print(visita.gardener.first_name)  # N queries (una por visita)
```

Si hay 100 visitas, se ejecutan 101 consultas a la base de datos. Con 1000, son 1001.

**Solución:** Usar `select_related` para relaciones ForeignKey (hace un JOIN en SQL) o `prefetch_related` para ManyToMany (hace 2 queries en total):

```python
# BIEN: 1 sola query con JOIN
visitas = VisitRequest.objects.select_related('gardener', 'service_type').all()
for visita in visitas:
    print(visita.gardener.first_name)  # No hace query adicional, ya lo tiene en memoria
```

Esto reduce las 101 consultas a solo 1. En el proyecto, el dashboard ya usa `select_related('service_type', 'gardener')` justamente para evitar este problema.

---

## A.3 Criterio y buenas prácticas

### 1. Si solo tengo 2 horas, ¿qué entrego primero?

Priorizaría así:

1. **Modelos + migraciones + admin (40 min):** Es lo primero porque es la base de todo lo demas. Sin los modelos no hay nada. Y registrar los modelos en el admin me da una interfaz funcional gratis para crear, editar y ver datos. Con esto ya puedo demostrar que el diseño de datos es correcto y que la logica de negocio funciona.

2. **Formulario publico de solicitud (30 min):** Un formulario con su vista, su Form de Django, y su template basico. No necesita ser bonito todavia. Lo importante es que un cliente pueda enviar una solicitud y que se guarde en la base de datos con las validaciones correctas.

3. **Vista del panel de empresa (30 min):** Una tabla simple que liste las solicitudes con su estado, protegida con `@login_required`. La funcionalidad de asignar jardinero puede ser simplificada o hacerse desde el admin.

4. **Tests básicos (15 min):** Al menos tests de creación de modelos, validación del formulario, y que las vistas respondan correctamente.

5. **README con instrucciones (5 min):** Para que quien revise pueda levantar el proyecto sin adivinar.

**¿Por qué este orden?** Porque voy de lo más fundamental a lo más accesorio. Los modelos son los cimientos. El formulario publico es el punto de entrada del negocio. El panel es donde la empresa trabaja. El diseño visual, el mapa, las animaciones y los detalles de UI se pueden pulir despues. Prefiero entregar algo funcional y completo en su logica a algo bonito pero incompleto.

---

### 2. Información mínima en un README

Pondría esto:

- **Qué es el proyecto:** Una línea que explique que hace. "Sistema de gestión de visitas para empresa de jardineria."

- **Requisitos previos:** Que necesitas tener instalado antes de empezar (Python 3.12+, PostgreSQL, pip).

- **Pasos de instalacion:** Comando por comando, copiables directamente:
  ```
  python -m venv env
  env\Scripts\activate
  pip install -r requirements.txt
  ```

- **Configuracion:** Qué variables de entorno hay que definir y dónde (archivo `.env`), y como crear la base de datos.

- **Migraciones y datos iniciales:**
  ```
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py load_initial_data
  ```

- **Cómo ejecutar:**
  ```
  python manage.py runserver
  ```

- **URLs principales:** Donde está el formulario, el panel, el admin.

- **Cómo correr los tests:**
  ```
  python manage.py test visits -v 2
  ```

La idea es que alguien clone el repo, siga los pasos en orden, y en 5 minutos tenga el sistema corriendo sin tener que preguntarme nada. Si tiene que adivinar algo, el README está incompleto.
