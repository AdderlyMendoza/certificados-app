# Certificados App

Plataforma web profesional para generar **certificados, constancias, diplomas, cartas y cualquier documento personalizado** de forma masiva, a partir de plantillas Word o PDF y datos de Excel.

---

## Tabla de contenidos

1. [Stack tecnológico](#1-stack-tecnológico)
2. [Arquitectura](#2-arquitectura)
3. [Instalación y puesta en marcha](#3-instalación-y-puesta-en-marcha)
   - [Con Docker (recomendado)](#con-docker-recomendado)
   - [Local sin Docker](#local-sin-docker)
4. [Manual de usuario](#4-manual-de-usuario)
   - [Inicio de sesión](#41-inicio-de-sesión)
   - [Dashboard](#42-dashboard)
   - [Módulo Plantillas](#43-módulo-plantillas)
   - [Editor Visual PDF](#44-editor-visual-pdf)
   - [Módulo Generaciones](#45-módulo-generaciones)
5. [Roles y permisos](#5-roles-y-permisos)
6. [Referencia de la API](#6-referencia-de-la-api)
7. [Referencia de variables de entorno](#7-referencia-de-variables-de-entorno)
8. [Migraciones de base de datos](#8-migraciones-de-base-de-datos)
9. [Tests](#9-tests)
10. [Resolución de problemas](#10-resolución-de-problemas)
11. [Roadmap](#11-roadmap)

---

## 1. Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2 |
| Base de datos | MySQL 8 (driver `asyncmy`) |
| Tareas pesadas | Celery + Redis |
| Monitoreo de tareas | Flower |
| Motores de documentos | PyMuPDF (PDF overlay), docxtpl (Word), qrcode, Pillow, ReportLab |
| Datos | Pandas, openpyxl, odfpy |
| Conversión docx → pdf | LibreOffice headless |
| Frontend | Vue 3, Vite, TypeScript, Pinia, Vue Router, TailwindCSS, Axios |
| Infraestructura | Docker Compose |

---

## 2. Arquitectura

El proyecto sigue **Clean Architecture** con separación estricta de capas:

```
Solicitud HTTP
      │
   API (FastAPI routers)          ← solo transporte y validación HTTP
      │
   Services (lógica de negocio)  ← orquestación, reglas de dominio
      │
   Repositories (acceso a datos) ← queries SQLAlchemy, sin lógica
      │
   Models (ORM)                  ← definición de tablas
      │
   MySQL 8
```

```
certificados-app/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                      # migraciones de BD
│   └── app/
│       ├── main.py                   # entrypoint FastAPI
│       ├── api/v1/                   # endpoints REST
│       │   ├── auth.py               # login, refresh, me
│       │   ├── users.py              # CRUD usuarios (admin)
│       │   ├── templates.py          # CRUD plantillas + upload + preview
│       │   ├── generations.py        # generación masiva
│       │   ├── qr.py                 # preview de QR
│       │   └── dashboard.py          # métricas
│       ├── core/                     # config, db, security, deps, excepciones
│       ├── models/                   # User, Template, Generation, AuditLog…
│       ├── schemas/                  # DTOs Pydantic (request/response)
│       ├── repositories/             # acceso a datos
│       ├── services/
│       │   ├── auth_service.py
│       │   ├── user_service.py
│       │   ├── template_service.py
│       │   ├── generation_service.py
│       │   └── documents/
│       │       ├── word_engine.py    # render docxtpl + conversión LibreOffice
│       │       ├── pdf_engine.py     # overlay PyMuPDF por coordenadas JSON
│       │       ├── qr_generator.py   # generación de QR configurable
│       │       └── dataset_reader.py # lectura Excel/CSV/ODS, detección columnas
│       ├── workers/
│       │   ├── celery_app.py
│       │   ├── tasks.py              # tarea run_generation (un PDF por fila)
│       │   └── db_sync.py            # sesión sync para Celery
│       └── utils/files.py            # gestión de archivos en disco
└── frontend/
    └── src/
        ├── components/editor/        # editor visual PDF (7 componentes)
        ├── views/                    # Login, Dashboard, Templates, Generations, Editor
        ├── stores/                   # auth, editor (Pinia)
        ├── services/                 # api, auth, template, generation
        ├── composables/              # useDarkMode
        └── types/index.ts            # tipos TypeScript del dominio
```

---

## 3. Instalación y puesta en marcha

### Con Docker (recomendado)

Requiere: Docker Desktop 24+ con Docker Compose v2.

```bash
# 1. Clona el repositorio
git clone <url-del-repo>
cd certificados-app

# 2. Crea el archivo de entorno
cp .env.example .env
```

Edita `.env` y cambia como mínimo:
```env
SECRET_KEY=tu-clave-secreta-larga-y-aleatoria
MYSQL_PASSWORD=una-contraseña-segura
MYSQL_ROOT_PASSWORD=otra-contraseña
```

```bash
# 3. Levanta todos los servicios
docker compose up --build
```

Espera unos 30-60 segundos a que MySQL arranque (hay health check). Cuando veas `Application startup complete`, la app está lista.

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Frontend | http://localhost:5173 | Interfaz web |
| API Swagger | http://localhost:8000/docs | Documentación interactiva |
| API ReDoc | http://localhost:8000/redoc | Documentación alternativa |
| Health check | http://localhost:8000/health | Estado del backend |
| Flower | http://localhost:5555 | Monitor de tareas Celery |
| MySQL | localhost:3306 | Base de datos |

**Usuario administrador creado automáticamente:**
- Email: `admin@certificados.local`
- Contraseña: `Admin1234!`
- (configurable en `.env` con `FIRST_SUPERUSER_EMAIL` y `FIRST_SUPERUSER_PASSWORD`)

---

### Local sin Docker

**Requisitos previos:**
- Python 3.13
- MySQL 8 corriendo (XAMPP, WAMP o nativo)
- Redis corriendo (o usa `docker run -d -p 6379:6379 redis:7-alpine`)
- LibreOffice instalado con `soffice` en el PATH (para convertir .docx a PDF)
- Node.js 22+

#### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env (en la raíz del proyecto)
# Ajusta MYSQL_HOST=127.0.0.1, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
# Crea la base de datos en MySQL primero:
#   CREATE DATABASE certificados CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Arrancar la API (crea las tablas automáticamente en primer arranque)
uvicorn app.main:app --reload --port 8000
```

En otra terminal, el worker Celery:

```bash
cd backend
.venv\Scripts\activate
celery -A app.workers.celery_app.celery_app worker --loglevel=info -P solo
# En Windows usa -P solo. En Linux puedes usar -P prefork con --concurrency=4
```

#### Frontend

```bash
cd frontend
cp .env.example .env        # VITE_API_BASE_URL=/api/v1 es el valor por defecto

npm install
npm run dev
```

---

## 4. Manual de usuario

### 4.1 Inicio de sesión

Abre http://localhost:5173. Verás la pantalla de login.

- **Email:** ingresa el email de tu cuenta
- **Contraseña:** ingresa tu contraseña
- Pulsa **Entrar**

El sistema emite un token de acceso (válido 30 minutos) y un token de refresco (7 días). El refresco es automático: si tu sesión expira mientras trabajas, la app la renueva sin interrumpirte.

**Contraseña olvidada:** un administrador puede resetearte la contraseña desde la gestión de usuarios.

---

### 4.2 Dashboard

La pantalla principal muestra 4 métricas en tiempo real:

| Tarjeta | Qué mide |
|---------|----------|
| Certificados generados | Total de documentos PDF producidos exitosamente |
| Plantillas | Número de plantillas registradas en el sistema |
| Generaciones | Número de trabajos de generación masiva |
| Errores | Documentos que fallaron durante alguna generación |

El sidebar izquierdo permite navegar entre módulos. El botón de luna/sol en la barra superior activa el **modo oscuro**.

---

### 4.3 Módulo Plantillas

Una plantilla es el molde del documento. Existen dos tipos:

| Tipo | Extensión | Cómo funciona |
|------|-----------|---------------|
| **Word** | `.docx` | Las variables `{{nombre}}` se reemplazan con docxtpl. Se convierte automáticamente a PDF con LibreOffice. |
| **PDF** | `.pdf` | El PDF actúa como fondo fijo. Se posicionan campos encima con el editor visual. |

#### Subir una nueva plantilla

1. Ve a **Plantillas** en el sidebar.
2. Pulsa **+ Nueva plantilla**.
3. Completa el formulario:
   - **Nombre:** identificador legible (ej. `Certificado de Asistencia 2026`).
   - **Categoría:** grupo opcional (ej. `Cursos`, `Diplomas`, `Eventos`).
   - **Archivo:** selecciona un `.docx` o `.pdf`.
4. Pulsa **Subir plantilla**.

El sistema analiza el archivo automáticamente:
- Para **Word**: detecta todas las variables `{{variable}}` declaradas en el documento y las muestra en la tabla.
- Para **PDF**: calcula las dimensiones de la primera página y prepara el canvas del editor visual.

#### Gestionar plantillas

Desde la tabla puedes:

- **✏️ Editor** (solo PDF): abre el editor visual de posicionamiento.
- **⎘ Duplicar**: crea una copia exacta con nombre `(copia)`. Útil para crear variaciones.
- **🗑 Eliminar**: elimina la plantilla y su archivo del disco. Acción irreversible.

#### Preparar una plantilla Word

Edita tu archivo `.docx` en Microsoft Word o LibreOffice Writer. Usa la sintaxis Jinja2 para las variables:

```
{{nombre}}           ← dato simple
{{apellido}}
{{dni}}
{{curso}}
{{fecha}}
{{empresa}}
{{cargo}}
{{codigo}}
```

El nombre de cada variable debe coincidir exactamente (incluidas mayúsculas) con el nombre de columna en tu Excel.

**Ejemplo de certificado Word:**
```
Certificamos que {{nombre}} {{apellido}},
con DNI {{dni}}, completó satisfactoriamente
el curso de {{curso}} el día {{fecha}}.
```

---

### 4.4 Editor Visual PDF

El editor visual es una herramienta de diseño que te permite posicionar campos de texto, variables, códigos QR e imágenes directamente sobre tu PDF, sin modificar el contenido original del documento.

**Cómo acceder:** en la tabla de Plantillas, pulsa **✏️ Editor** en una plantilla de tipo PDF.

El editor se abre en pantalla completa con esta distribución:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Plantillas  [Nombre]  [NO GUARDADO]  [+ Campo]  [↩ ↪]  [− 100% +] [Ajustar] [Cuadrícula ☑] [Snap ☑] [10px ▾]  [💾 Guardar] │
├─────────────┬──────────────────────────────────────────────────┬─────────────┤
│   CAPAS     │                                                  │ PROPIEDADES │
│             │            Canvas (PDF como fondo)               │             │
│  ↕ reorden  │     [campo arrastrable] [campo arrastrable]      │  Nombre     │
│  por drag   │                                                  │  X / Y      │
│             │     Cuadrícula de puntos (configurable)          │  W / H      │
│  ✕ eliminar │                                                  │  Fuente     │
│             │            Regla numérica superior               │  Tamaño     │
└─────────────┴──────────────────────────────────────────────────┴─────────────┘
```

#### Tipos de campo

| Icono | Tipo | Descripción |
|-------|------|-------------|
| T | **Texto fijo** | Texto estático igual en todos los documentos (ej. "República de Colombia") |
| {} | **Variable** | Dato que cambia por fila del Excel (ej. `{{nombre}}`) |
| ⊡ | **Código QR** | QR generado automáticamente con contenido configurable |
| 📅 | **Fecha** | Variable de tipo fecha del dataset |
| # | **Número** | Variable numérica del dataset |
| 🖼 | **Imagen** | Imagen por nombre de columna |
| ✍ | **Firma** | Imagen de firma por nombre de columna |
| ▐▌ | **Código de barras** | Código de barras (en desarrollo) |

#### Agregar un campo

1. Pulsa **+ Campo** en la barra de herramientas.
2. Elige el tipo de campo en el paso 1.
3. En el paso 2, escribe el nombre:
   - Para **Variable**: usa el mismo nombre que la columna del Excel (ej. `nombre`). Las variables ya detectadas en la plantilla aparecen como botones de sugerencia.
   - Para **Texto fijo**: escribe un ID interno cualquiera (ej. `titulo_principal`).
   - Para **QR**: el nombre por defecto es `qr`.
4. Pulsa **Agregar**. El campo aparece centrado en el canvas.

#### Mover y posicionar campos

- **Arrastrar:** haz clic y arrastra cualquier campo a su posición.
- **Precisión:** en el panel **Propiedades** (derecha) escribe las coordenadas exactas en **X** e **Y** (en puntos PDF).
- **Snap:** con Snap activado, los campos se alinean automáticamente a la cuadrícula al soltarlos.
- **Flechas del teclado:** con un campo seleccionado, usa ↑↓←→ para moverlo 1px. Con Shift, se mueve 10px.

#### Redimensionar campos

Selecciona un campo. Aparecen **8 manejadores blancos** (azules) en los bordes y esquinas. Arrastra cualquiera de ellos para cambiar el tamaño. También puedes escribir el ancho (**W**) y alto (**H**) exacto en el panel de Propiedades.

#### Panel de Propiedades (columna derecha)

Cuando tienes un campo seleccionado:

**Identificación**
- **Nombre / ID:** cambia el nombre del campo (debe coincidir con la columna Excel para variables).
- **Valor fijo:** (solo campos tipo *Texto fijo*) el texto literal que aparecerá.

**Posición y tamaño**
- **X, Y:** coordenadas en puntos PDF desde la esquina superior izquierda.
- **Ancho, Alto:** dimensiones en puntos. Déjalos en blanco para tamaño automático en texto.
- **Rotación:** ángulo en grados (0-360).

**Tipografía** (solo campos de texto)
- **Fuente:** Helvetica, Times o Courier.
- **Tamaño:** en puntos (recomendado: 12-18 para texto normal, 24-36 para títulos).
- **Color:** selector visual o código hexadecimal (#RRGGBB).
- **B** Negrita / *I* Cursiva.
- **Alineación:** izquierda, centro o derecha.

#### Panel de Capas (columna izquierda)

Lista todos los campos del documento. El campo más arriba en la lista es el más adelante visualmente.

- **Clic** en una capa → selecciona ese campo en el canvas.
- **Drag vertical** → reordena las capas.
- **↑ / ↓** → sube o baja una posición.
- **⎘** → duplica el campo seleccionado.
- **🗑** → elimina el campo seleccionado.

#### Barra de herramientas

| Control | Función |
|---------|---------|
| ← Plantillas | Vuelve a la lista (pide confirmación si hay cambios sin guardar) |
| + Campo | Abre el diálogo para añadir un nuevo campo |
| ↩ (Ctrl+Z) | Deshace el último cambio |
| ↪ (Ctrl+Y) | Rehace el cambio deshecho |
| − / + | Reduce / amplía el zoom |
| % | Nivel de zoom actual |
| Ajustar | Calcula el zoom para que la página quepa en pantalla |
| Cuadrícula | Muestra u oculta la cuadrícula de puntos |
| Snap | Activa/desactiva el ajuste automático a la cuadrícula |
| 10 px | Tamaño de celda de la cuadrícula (5 / 10 / 20 / 50 px) |
| 💾 Guardar | Guarda el layout en la base de datos |

#### Atajos de teclado

| Tecla | Acción |
|-------|--------|
| `Supr` / `Backspace` | Elimina el campo seleccionado |
| `Ctrl + D` | Duplica el campo seleccionado |
| `Ctrl + Z` | Deshacer |
| `Ctrl + Y` / `Ctrl + Shift + Z` | Rehacer |
| `↑ ↓ ← →` | Mueve el campo 1 px |
| `Shift + ↑ ↓ ← →` | Mueve el campo 10 px |
| `Escape` | Deselecciona el campo actual |

#### Sistema de coordenadas

El canvas usa el sistema de coordenadas de PDF: **origen en la esquina superior izquierda**, X crece hacia la derecha, Y crece hacia abajo. Las unidades son **puntos PDF** (1 punto = 1/72 de pulgada).

Tamaños de página de referencia:
- A4 vertical: 595 × 842 pt
- A4 horizontal: 842 × 595 pt
- Carta vertical: 612 × 792 pt
- Carta horizontal: 792 × 612 pt

#### Guardar y versiones

Al pulsar **💾 Guardar**, el layout se almacena como JSON en la base de datos. La próxima vez que abras el editor, el diseño estará exactamente como lo dejaste.

El sistema mantiene un historial de versiones de la plantilla. Cada vez que guardas o subes un archivo nuevo se crea un snapshot automático.

---

### 4.5 Módulo Generaciones

Una **generación** es el proceso de crear un documento PDF por cada fila de un dataset Excel/CSV/ODS, usando una plantilla.

#### Wizard de nueva generación (3 pasos)

**Paso 1 — Configuración**

- **Nombre de la generación:** nombre descriptivo del lote (ej. `Certificados Taller Mayo 2026`).
- **Plantilla:** elige la plantilla a usar. Se muestran las variables detectadas en ella para que puedas verificar que coincidan con tus columnas de Excel.

**Paso 2 — Dataset**

Sube el archivo de datos:
- Formatos aceptados: `.xlsx`, `.xls`, `.csv`, `.ods`
- Tamaño máximo: 25 MB (configurable en `.env`)

El sistema analiza el archivo y muestra:
- **Columnas detectadas**: cada columna se convierte automáticamente en una variable `{{columna}}`.
- **Vista previa**: primeras filas del dataset.
- **Errores**: columnas duplicadas, columnas sin nombre, etc.

> **Regla clave:** el nombre de cada columna del Excel debe coincidir con el nombre de variable en la plantilla. Si tu plantilla tiene `{{nombre}}` y tu Excel tiene una columna llamada `nombre`, funcionará automáticamente sin configuración adicional.

**Paso 3 — Confirmar y generar**

Revisa el resumen:
- Nombre de la generación
- Plantilla seleccionada
- Número de documentos a generar

Pulsa **⚡ Iniciar generación**. El trabajo se encola en Celery y puedes ver el progreso inmediatamente.

#### Monitorear el progreso

La vista de Generaciones muestra en tiempo real:
- **Barra de progreso** con el porcentaje completado.
- Contador `X / Y documentos`.
- Contador de errores (filas que fallaron).
- Estado: `pending` → `processing` → `completed` / `failed` / `cancelled`.

El frontend consulta el backend automáticamente cada 2,5 segundos mientras haya trabajos activos.

#### Descargar resultados

Cuando el estado cambia a `completed`, aparece el botón **⬇ ZIP**. El ZIP contiene todos los PDFs generados, nombrados con el formato:

```
0001_Ana García.pdf
0002_Carlos López.pdf
0003_María Fernández.pdf
...
```

#### Cancelar una generación

Mientras el estado es `pending` o `processing`, el botón **✕ Cancelar** detiene la tarea en Celery. Los documentos ya generados antes de la cancelación no se eliminan.

#### Errores parciales

Si algunas filas fallan (datos inválidos, imagen no encontrada, etc.), la generación continúa con las demás filas. Los errores se registran por fila y el ZIP solo incluye los PDFs generados exitosamente.

---

## 5. Roles y permisos

| Rol | Plantillas | Generaciones | Usuarios | Logs |
|-----|-----------|--------------|----------|------|
| **admin** | CRUD completo | CRUD completo | CRUD completo | Lectura |
| **operator** | CRUD completo | CRUD completo | — | — |
| **auditor** | Solo lectura | Solo lectura | — | Lectura |

Un administrador puede crear usuarios y asignar roles desde la API (endpoint `POST /api/v1/users`). La gestión de usuarios en la UI está disponible vía la documentación Swagger en `/docs`.

---

## 6. Referencia de la API

La API sigue REST con respuestas JSON. Todos los endpoints (excepto `/health` y `/api/v1/auth/login`) requieren el header:

```
Authorization: Bearer <access_token>
```

### Autenticación

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| POST | `/api/v1/auth/login` | Login. Body: form-data `username` (email) + `password`. Devuelve access y refresh token. |
| POST | `/api/v1/auth/refresh` | Renueva el access token. Body JSON: `{"refresh_token": "..."}` |
| GET | `/api/v1/auth/me` | Devuelve el usuario autenticado actual. |

### Plantillas

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| GET | `/api/v1/templates` | Lista plantillas (paginado, filtro por `category`). |
| POST | `/api/v1/templates` | Sube nueva plantilla. Multipart: `name`, `file`, `description?`, `category?`. |
| GET | `/api/v1/templates/{id}` | Detalle de una plantilla. |
| PATCH | `/api/v1/templates/{id}` | Actualiza nombre, layout, qr_config o status. |
| DELETE | `/api/v1/templates/{id}` | Elimina plantilla y su archivo. |
| POST | `/api/v1/templates/{id}/duplicate` | Duplica la plantilla. |
| GET | `/api/v1/templates/{id}/variables` | Lista de variables detectadas. |
| GET | `/api/v1/templates/{id}/versions` | Historial de versiones. |
| GET | `/api/v1/templates/{id}/preview` | PNG de la página (param `page=0`). Solo plantillas PDF. |

### Generaciones

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| POST | `/api/v1/generations/preview-dataset` | Vista previa del dataset. Multipart: `file`. |
| GET | `/api/v1/generations` | Lista generaciones (paginado). |
| POST | `/api/v1/generations` | Crea generación. Multipart: `name`, `template_id`, `file`. |
| GET | `/api/v1/generations/{id}` | Estado y progreso de una generación. |
| POST | `/api/v1/generations/{id}/start` | Encola la generación en Celery. |
| POST | `/api/v1/generations/{id}/cancel` | Cancela la tarea en Celery. |
| GET | `/api/v1/generations/{id}/download` | Descarga el ZIP (streaming). |

### Dashboard y utilidades

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| GET | `/api/v1/dashboard/stats` | Métricas globales. |
| GET | `/api/v1/dashboard/activity` | Últimas 15 acciones del log. |
| POST | `/api/v1/qr/preview` | Genera un PNG de QR. Body JSON: `content` + `QRConfig`. |
| GET | `/health` | Estado del backend (sin autenticación). |

El formato del layout JSON que acepta `PATCH /templates/{id}`:

```json
{
  "layout": {
    "page_width": 595.28,
    "page_height": 841.89,
    "fields": [
      {
        "name": "nombre",
        "type": "variable",
        "page": 0,
        "x": 250,
        "y": 420,
        "width": 300,
        "height": 30,
        "font": "Helvetica",
        "font_size": 18,
        "color": "#000000",
        "bold": false,
        "italic": false,
        "align": "center",
        "rotation": 0,
        "value": null
      },
      {
        "name": "qr",
        "type": "qr",
        "page": 0,
        "x": 460,
        "y": 50,
        "width": 90,
        "height": 90,
        "font": "Helvetica",
        "font_size": 14,
        "color": "#000000",
        "bold": false,
        "italic": false,
        "align": "left",
        "rotation": 0,
        "value": null
      }
    ]
  }
}
```

---

## 7. Referencia de variables de entorno

Copia `.env.example` a `.env` y ajusta según tu entorno.

| Variable | Valor por defecto | Descripción |
|----------|------------------|-------------|
| `APP_NAME` | `Certificados App` | Nombre de la aplicación |
| `APP_ENV` | `development` | `development` o `production` |
| `DEBUG` | `true` | Logs SQL y recarga automática |
| `API_V1_PREFIX` | `/api/v1` | Prefijo de la API |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:5173"]` | Orígenes CORS permitidos |
| `MYSQL_HOST` | `mysql` | Host de MySQL (`mysql` en Docker, `127.0.0.1` en local) |
| `MYSQL_PORT` | `3306` | Puerto MySQL |
| `MYSQL_USER` | `cert_user` | Usuario de MySQL |
| `MYSQL_PASSWORD` | `cert_pass` | Contraseña MySQL |
| `MYSQL_DATABASE` | `certificados` | Nombre de la base de datos |
| `REDIS_HOST` | `redis` | Host Redis (`redis` en Docker, `127.0.0.1` en local) |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | URL del broker Celery |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Backend de resultados Celery |
| `SECRET_KEY` | *(cambiar)* | Clave para firmar JWT. Genera con: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Vigencia del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Vigencia del refresh token |
| `FIRST_SUPERUSER_EMAIL` | `admin@certificados.local` | Email del admin creado en el primer arranque |
| `FIRST_SUPERUSER_PASSWORD` | `Admin1234!` | Contraseña del admin inicial |
| `UPLOAD_DIR` | `/app/uploads` | Directorio para plantillas subidas |
| `GENERATED_DIR` | `/app/generated` | Directorio para PDFs generados y ZIPs |
| `MAX_UPLOAD_MB` | `25` | Tamaño máximo de archivo subido |
| `SOFFICE_BIN` | `soffice` | Ruta al ejecutable de LibreOffice |

---

## 8. Migraciones de base de datos

**En desarrollo** las tablas se crean automáticamente al arrancar (`init_models()` en el lifespan de FastAPI). No necesitas hacer nada.

**En producción** usa Alembic para control de versiones del schema:

```bash
cd backend

# Primera vez: genera la migración inicial desde los modelos actuales
alembic revision --autogenerate -m "init"

# Aplica todas las migraciones pendientes
alembic upgrade head

# Ver el estado actual
alembic current

# Revertir una migración
alembic downgrade -1
```

---

## 9. Tests

```bash
cd backend

# Instala dependencias de desarrollo
pip install pytest pytest-asyncio

# Ejecuta todos los tests
pytest

# Con detalle
pytest -v

# Solo un módulo
pytest tests/test_security.py
```

Tests incluidos:

| Archivo | Qué prueba |
|---------|-----------|
| `tests/test_security.py` | Hash de contraseñas, creación y validación de JWT, comprobación del tipo de token |
| `tests/test_qr.py` | Generación de PNG de QR, firma de archivo, nivel de corrección de errores |
| `tests/test_pdf_engine.py` | Conversión hex→RGB, resolución de fuentes (bold/italic), sustitución de variables en templates |

---

## 10. Resolución de problemas

**El backend no conecta con MySQL**
- Verifica que MySQL esté corriendo y accesible.
- En Docker, espera el health check (puede tardar 30s en el primer arranque).
- Comprueba `MYSQL_HOST` (usa `mysql` dentro de Docker, `127.0.0.1` en local).
- Asegúrate de que la base de datos exista: `CREATE DATABASE certificados CHARACTER SET utf8mb4;`

**La conversión de Word a PDF falla**
- LibreOffice debe estar instalado y `soffice` en el PATH.
- Verifica con: `soffice --version`
- En Docker está incluido en el Dockerfile. En Windows, instala LibreOffice y agrega su carpeta `program` al PATH del sistema.
- En producción Linux: `apt-get install libreoffice-writer`

**El worker Celery no procesa tareas**
- Verifica que Redis esté corriendo: `redis-cli ping` → debe devolver `PONG`.
- Comprueba los logs del worker: `docker compose logs worker`
- En Windows en modo local, usa `-P solo` para evitar problemas de multiprocessing.

**El editor visual PDF muestra la página en blanco**
- La plantilla debe ser de tipo PDF (`.pdf`).
- Verifica que el archivo exista en `UPLOAD_DIR`.
- Revisa los logs del backend para errores de PyMuPDF.
- El endpoint `GET /api/v1/templates/{id}/preview` debe devolver un PNG (puedes probarlo en `/docs`).

**Las variables no se reemplazan en Word**
- Verifica que la sintaxis sea exactamente `{{nombre_variable}}` con doble llave.
- El nombre debe coincidir exactamente (mayúsculas incluidas) con la columna del Excel.
- Abre el docx con un editor de texto y busca el marcador: a veces Word divide el texto en varios `<w:r>` y rompe la variable. Escríbela de nuevo directamente en el documento.

**El ZIP de descarga está vacío**
- Si todos los ítems fallaron, el ZIP existirá pero no tendrá archivos.
- Revisa los errores en la pantalla de generaciones.
- Consulta los logs del worker: `docker compose logs worker`

**Error `cryptography` al conectar con MySQL**
- Instala: `pip install cryptography`
- Ya incluida en `requirements.txt`. Si persiste, verifica la versión de `asyncmy` y `pymysql`.

---

## 11. Roadmap

- [x] **Fase 1** — Fundación backend: arquitectura Clean, modelos, auth JWT, motores Word/PDF/QR/dataset, Celery, Docker, Alembic
- [x] **Fase 2** — Frontend funcional: login, dashboard, gestión de plantillas (upload, tabla, modal), gestión de generaciones (wizard 3 pasos, polling, descarga ZIP)
- [x] **Fase 3** — Editor visual PDF: drag & drop, resize (8 handles), snap/grid, zoom, undo/redo, capas, panel propiedades, 8 tipos de campo, atajos de teclado
- [ ] **Fase 4** — Historial y auditoría: UI de logs de auditoría, descarga individual por ítem, reintentos de generaciones fallidas
- [ ] **Fase 5** — Funcionalidades avanzadas: código de barras funcional, subida de imágenes/firmas en el editor, previsualización del documento final antes de generar, gestión de usuarios en la UI
- [ ] **Fase 6** — Producción: configuración NGINX, HTTPS, backups automáticos, métricas Prometheus, CI/CD

---

## Licencia

Privado — © 2026.
