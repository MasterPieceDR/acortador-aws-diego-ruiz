# Acortador de enlaces en AWS — Diego Ruiz

Aplicación web para acortar enlaces. La interfaz (HTML, CSS y JavaScript) se publica en **Amazon S3**, la API **FastAPI** se ejecuta en **Amazon EC2** y los enlaces se guardan en **Amazon DynamoDB**.

```
Navegador ──(fetch POST /shorten)──▶ EC2: FastAPI ──(PutItem / GetItem)──▶ DynamoDB
    ▲                                    │
    └──── S3 (index.html, css, js) ──────┘  GET /{short_code} → 307 Redirect
```

## Estructura del proyecto

```
acortador-aws-diego-ruiz/
├── backend/
│   ├── src/
│   │   ├── crud/            # Acceso a datos: PutItem y GetItem en DynamoDB
│   │   ├── database/        # Conexión Boto3 a DynamoDB (sin access keys)
│   │   ├── models/          # Modelo de dominio ShortLink
│   │   ├── routers/         # Endpoints (health, shorten, urls, redirect)
│   │   ├── schemas/         # Contratos Pydantic de entrada/salida
│   │   ├── security/        # Validación de URL/UUID, CORS y cabeceras
│   │   ├── services/        # Lógica de negocio: genera el UUID y el short_url
│   │   ├── config.py        # Configuración desde variables de entorno
│   │   └── main.py          # Crea la app y une los módulos con routers
│   ├── scripts/create_table.py  # Crea la tabla (local o AWS)
│   ├── requirements.txt
│   ├── requirements-dev.txt     # + DynamoDB local para desarrollo
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   ├── js/config.js         # URL del backend (API_BASE_URL)
│   ├── js/app.js            # Validación, fetch(), copiar enlace
│   ├── fonts/               # Overpass (SIL OFL), servida desde el propio bucket
│   ├── favicon.svg
│   └── robots.txt
└── deploy/
    ├── setup_ec2.sh             # Instala y despliega el backend en EC2
    ├── pruebas.sh               # Pruebas de los endpoints contra la API desplegada
    ├── shortener.service        # Servicio systemd para EC2
    ├── iam-policy-dynamodb.json # Política de mínimo privilegio del rol IAM
    └── s3-bucket-policy.json    # Lectura pública del sitio estático
```

El proyecto no usa archivos `__init__.py`: las carpetas de `src/` funcionan como *namespace packages* de Python 3. `fastapi run src/main.py` agrega `src/` al `sys.path`, por eso los módulos se importan directamente (`from config import ...`).

## Endpoints

| Método | Ruta | Descripción | Respuestas |
|---|---|---|---|
| POST | `/shorten` | Valida la URL, genera un UUID v4 y guarda el enlace | 201, 422, 503 |
| GET | `/{short_code}` | Busca el UUID en DynamoDB y redirige | **307**, 404, 503 |
| GET | `/urls/{short_code}` | Devuelve el enlace en JSON | 200, 404, 503 |
| GET | `/health` | Estado del servicio | 200 |

Documentación interactiva: `http://<host>:8000/docs`

### Manejo de errores

- **URL inválida (422):** vacía, con espacios, sin `http://`/`https://`, otro esquema (`ftp:`, `javascript:`), dominio inválido, con usuario/contraseña, más de 2048 caracteres, o que apunte al propio acortador (evita bucles).
- **JSON mal formado o sin `original_url` (422).**
- **UUID inexistente o con formato inválido (404).**
- **DynamoDB no disponible o sin permisos (503).**
- **Error inesperado (500)**, registrado en el log del servicio.

La interfaz repite las validaciones antes de enviar la petición y además informa cuando el backend no responde (sin conexión, CORS o tiempo de espera de 10 s).

## Ejecutar en local (sin AWS)

En local se usa una DynamoDB local (`moto_server`), así no hace falta tener nada creado en AWS.

**Terminal 1: base de datos local**

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
moto_server -p 8001
```

**Terminal 2: crear la tabla y levantar la API**

```powershell
cd backend
.venv\Scripts\activate
copy .env.example .env           # Linux/macOS: cp .env.example .env
python scripts/create_table.py
fastapi dev src/main.py
```

**Terminal 3: interfaz web**

```powershell
cd frontend
python -m http.server 5500
```

Abrir `http://localhost:5500`. La DynamoDB local guarda los datos en memoria: al cerrar `moto_server` se borran y hay que volver a ejecutar `python scripts/create_table.py`.

Para usar la tabla real de AWS desde tu PC, deja vacío `DYNAMODB_ENDPOINT_URL` en `.env` y configura las credenciales de AWS Academy en `~/.aws/credentials`.

## Despliegue en AWS

1. **DynamoDB:** crear la tabla `shortener-links-diego` (clave de partición `short_code`, String).
2. **IAM:** rol para EC2 con la política de `deploy/iam-policy-dynamodb.json` (solo `PutItem` y `GetItem`).
3. **EC2 (Amazon Linux 2023):** asociar el rol, abrir el puerto 8000 y restringir SSH. Dentro de la instancia:
   ```bash
   curl -O https://raw.githubusercontent.com/MasterPieceDR/acortador-aws-diego-ruiz/main/deploy/setup_ec2.sh
   bash setup_ec2.sh http://<bucket>.s3-website-us-east-1.amazonaws.com
   ```
   Instala Python 3.11 (Amazon Linux 2023 trae 3.9 y FastAPI 0.162 requiere 3.10 o superior), crea el `.env` y deja la API en systemd.
4. **S3:** bucket con alojamiento de sitio web estático y la política de `deploy/s3-bucket-policy.json`. Cambiar `API_BASE_URL` en `frontend/js/config.js` por `http://<ip-publica-ec2>:8000` y subir la carpeta `frontend/`.
5. **Pruebas:** `bash deploy/pruebas.sh http://<ip-publica-ec2>:8000`.

## Variables de entorno

| Variable | Ejemplo | Uso |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Región de DynamoDB |
| `DYNAMODB_TABLE` | `shortener-links-diego` | Tabla de enlaces |
| `PUBLIC_BASE_URL` | `http://<ip-publica-ec2>:8000` | Base del `short_url` |
| `CORS_ORIGINS` | `http://<bucket>.s3-website-us-east-1.amazonaws.com` | Orígenes permitidos |
| `DYNAMODB_ENDPOINT_URL` | *(vacío)* | Solo para DynamoDB Local |
| `MAX_URL_LENGTH` | `2048` | Longitud máxima de URL |

Las credenciales de AWS **nunca** se guardan en el código ni en `.env`: en EC2 se usan las credenciales temporales del rol IAM.

## Tabla DynamoDB

| Atributo | Tipo | Rol |
|---|---|---|
| `short_code` | String (UUID v4) | Clave de partición |
| `original_url` | String | Destino de la redirección |
| `created_at` | String (ISO 8601 UTC) | Fecha de creación |

---
Autor: **Diego Ruiz** — Universidad Internacional del Ecuador (UIDE)
