# Microservicios Python para OPA + Envoy POC

Este directorio contiene dos microservicios desarrollados en Python (Flask) diseñados para interactuar en un entorno de malla/proxy con **Envoy** y **Open Policy Agent (OPA)**.

---

## 📁 Estructura

```text
4.-apps/
├── client-app-1.0.0/
│   ├── Dockerfile
│   ├── client.py
│   ├── requirements.txt
│   └── .dockerignore
└── server-app-1.0.0/
    ├── Dockerfile
    ├── server.py
    ├── requirements.txt
    └── .dockerignore
```

---

## 🚀 Servicios y Endpoints

### 1. Client Service (`client-app-1.0.0`)
Microservicio cliente que puede recibir peticiones HTTP y/o consumir el servicio servidor upstream a través de Envoy/OPA.

* **Endpoints**:
  * `GET /api/client/v1` / `POST /api/client/v1`: Endpoint principal.
    * Si se configura `TARGET_URL` o se pasa `?target=http://...`, realiza la llamada al servicio upstream (ej. el servidor) y reenvía cabeceras de autorización (`Authorization: Bearer <token>`).
  * `GET /health`: Healthcheck para sondas de Kubernetes (`livenessProbe` / `readinessProbe`).
  * `GET /`: Metadatos y lista de endpoints.

* **Variables de Entorno principales**:
  * `SERVER_PORT` / `APP_PORT` / `CONTAINER_SERVICE_PORT`: Puerto de escucha (por defecto `5000`).
  * `SERVER_HOST`: Host de enlace (por defecto `0.0.0.0`).
  * `TARGET_URL` / `SERVER_URL`: URL upstream a la cual consultar (ej. `http://server-app:5000/api/server/v1`).
  * `DEFAULT_AUTH_TOKEN`: Token JWT por defecto para enviar upstream si la petición no incluye uno.
  * `RUN_BACKGROUND_LOOP`: (`true`/`false`) Permite ejecutar un bucle en segundo plano generando tráfico continuo a `TARGET_URL` cada `REQUEST_INTERVAL` segundos (útil para pruebas automatizadas de OPA).
  * `SSL`: (`true`/`false`) Activa TLS si se montan certificados en `CERT_PATH` y `KEY_PATH`.

---

### 2. Server Service (`server-app-1.0.0`)
Microservicio backend objetivo protegido por las políticas de OPA a través del filtro `ext_authz` de Envoy.

* **Endpoints**:
  * `GET /api/server/v1` / `POST /api/server/v1`: Endpoint principal.
    * Devuelve información del host, IP cliente detectada (`X-Forwarded-For`), cabeceras recibidas e inspección del payload JWT (claims como `role`, `sub`, etc.).
  * `GET /health`: Healthcheck para sondas de Kubernetes (`livenessProbe` / `readinessProbe`).
  * `GET /`: Metadatos y lista de endpoints.

* **Variables de Entorno principales**:
  * `SERVER_PORT` / `APP_PORT` / `CONTAINER_SERVICE_PORT`: Puerto de escucha (por defecto `5000`).
  * `SERVER_HOST`: Host de enlace (por defecto `0.0.0.0`).
  * `SSL`: (`true`/`false`) Activa TLS si se configuran `CERT_PATH` y `KEY_PATH` (por defecto se ejecuta en HTTP para desarrollo ágil y compatibilidad).

---

## 🐳 Construcción de Imágenes Docker

### Construir Client App
```bash
docker build -t client-app:1.0.0 4.-apps/client-app-1.0.0
```

### Construir Server App
```bash
docker build -t server-app:1.0.0 4.-apps/server-app-1.0.0
```

---

## 🧪 Ejemplo de Ejecución Local con Docker

1. **Crear red Docker:**
   ```bash
   docker network create opa-net
   ```

2. **Iniciar Server:**
   ```bash
   docker run -d --name server-app --network opa-net -p 5001:5000 server-app:1.0.0
   ```

3. **Iniciar Client apuntando al Server:**
   ```bash
   docker run -d --name client-app --network opa-net -p 5002:5000 \
     -e TARGET_URL=http://server-app:5000/api/server/v1 client-app:1.0.0
   ```

4. **Probar Client:**
   ```bash
   curl http://localhost:5002/api/client/v1
   ```
