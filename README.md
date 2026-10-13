# OPA + Envoy Integration POC (Python Microservices)

Open Policy Agent (OPA) como motor de políticas de autorización desacoplado para microservicios en Kubernetes. Integrado mediante un sidecar de **Envoy Proxy**, el cual intercepta el tráfico entrante, termina TLS y delega las decisiones de autorización a OPA a través del filtro `ext_authz` (gRPC).

Este repositorio está preparado como un POC público y educativo que demuestra:
1. Microservicios desacoplados en **Python (Flask)**: `client-app` (`/api/client/v1`) y `server-app` (`/api/server/v1`).
2. Patrón **Envoy Sidecar** con `proxy-init` (iptables) para interceptación transparente de tráfico.
3. Autorización basada en políticas Rego con **Open Policy Agent (OPA)** e inspección de JWT.
4. Terminación **TLS/HTTPS** y gestión de certificados con extensiones SAN.

---

## 🏗️ Arquitectura de Flujo de Tráfico

```text
Cliente Externo / Ingress / Client App
                  │
                  ▼ (HTTPS :8443)
┌─────────────────────────────────────────────────────────┐
│ Pod: server-app (Namespace: opa-ms)                     │
│                                                         │
│   iptables (proxy-init)                                 │
│         │                                               │
│         ▼                                               │
│   ┌──────────────┐         gRPC :9191                   │
│   │ Envoy Proxy  │──────────────────────────┐           │
│   │ (:8443)      │                          │           │
│   │ [TLS Term.]  │◀──────────────────────┐  │           │
│   └──────┬───────┘   Allow / Deny        │  │           │
│          │                               │  ▼           │
│          ▼ (HTTP :5000)               ┌──────────────┐  │
│   ┌──────────────┐                    │ OPA Service  │  │
│   │ server.py    │                    │ (ext_authz)  │  │
│   │ Flask App    │                    └──────────────┘  │
│   └──────────────┘                                      │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura del Repositorio

```text
.
├── 1.-core/                            # Utilidades core y banner
│   └── banner.sh
│
├── 2.-cluster/                         # Configuración del cluster local KinD y CoreDNS
│   ├── kind-configuration.yaml         # Definición de KinD (ingress ports 80/443 + registry mirror)
│   └── coredns-configmap.yaml          # Reescribe dominios alternativos a server-app.opa-ms
│
├── 3.-certificates/                    # Certificados TLS X.509 y configuración OpenSSL
│   ├── san.cnf                         # Config OpenSSL con SANs para opa-ms
│   ├── generate.sh                     # Script para generar certs con OpenSSL
│   ├── server.crt                      # Certificado X.509 (válido hasta 2028)
│   └── server.key                      # Clave privada RSA 2048 bits
│
├── 4.-apps/                            # Microservicios Python Flask
│   ├── client-app-1.0.0/               # Endpoint: /api/client/v1
│   │   ├── Dockerfile
│   │   ├── client.py
│   │   └── requirements.txt
│   ├── server-app-1.0.0/               # Endpoint: /api/server/v1
│   │   ├── Dockerfile
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── ms-deploy.sh                    # Script de despliegue de microservicios
│   ├── ms-prepare.sh                   # Script de preparación de recursos
│   └── serviceaccount/                 # Definiciones de ServiceAccount de referencia
│
├── 5.-envoy/                           # Configuraciones de Envoy Proxy
│   ├── envoy-python-apps.yaml          # Config de Envoy para microservicios Python
│   ├── envoy-ms.yaml                   # Config de Envoy original (referencia)
│   ├── envoy-example.yaml              # Configuración de ejemplo
│   └── 01-configmap-envoy-create.sh    # Script de creación del ConfigMap de Envoy
│
├── 6.-opa/                             # Manifiestos y políticas OPA
│   ├── opa-deployment.yaml             # Despliegue de OPA en namespace opa
│   ├── opa-config.yaml                 # Configuración de OPA daemon
│   ├── opa-install.sh                  # Script de instalación de OPA
│   ├── opa-prepare.sh                  # Script de preparación de OPA
│   └── regos/                          # Políticas Rego (reglas para Python y JWT)
│       ├── policy.rego
│       └── policy_test.rego
│
├── 7.-k8s-manifests/                   # Manifiestos de despliegue para Kubernetes
│   ├── client-app-1.0.0/               # Client Deployment, Service y Secret
│   │   ├── client-secret.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── server-app-1.0.0/               # Server Deployment, Service, Ingress y Secret
│   │   ├── deployment.yaml
│   │   ├── ingress.yaml
│   │   ├── secret-tls.yaml
│   │   ├── server-backend-ca.yaml
│   │   └── service.yaml
│   ├── deploy.sh                       # Script para desplegar todo en el namespace opa-ms
│   ├── delete.sh                       # Script para eliminar todos los recursos
│   ├── namespace.yaml                  # Definición del namespace opa-ms
│   └── rbac.yaml                       # ServiceAccount, ClusterRole y Binding
│
└── Makefile
```

---

## 🛠️ Simulación Completa con KinD y Makefile

El repositorio incluye un [`Makefile`](Makefile) para automatizar la simulación completa del entorno: creación del registry Docker local (`registry:3`), provisión del cluster KinD multi-nodo con puertos Ingress (80/443), compilación/push de imágenes, despliegue de OPA y de los microservicios con Envoy.

### Comandos Principales

```bash
# Ver todos los targets disponibles
make help

# 1. Despliegue completo automatizado (Registry + KinD + Imágenes + OPA + Apps)
make install
# (o alternativamente: make up)

# 2. Comprobar estado de los pods y servicios
make status

# 3. Ver logs en tiempo real
make logs-opa              # Decisiones de autorización en OPA
make logs-server           # Logs del microservicio servidor
make logs-envoy-server     # Logs del sidecar de Envoy en server-app

# 4. Limpieza
make clean                 # Elimina apps y OPA del cluster
make down                  # Destruye el cluster KinD
make dist-clean            # Limpieza total (apps + OPA + cluster + registry)
```

---

## 🚀 Despliegue Manual Paso a Paso

Si prefieres desplegar manualmente sobre un cluster existente:

### 1. Desplegar OPA

```bash
6.-opa/opa-install.sh
```

### 2. Desplegar los Microservicios con Envoy y Certificados

Utiliza el script automatizado en [`7.-k8s-manifests/deploy.sh`](7.-k8s-manifests/deploy.sh):

```bash
chmod +x 7.-k8s-manifests/deploy.sh
./7.-k8s-manifests/deploy.sh
```

El script se encarga de:
1. Crear el namespace `opa-ms`.
2. Crear el ConfigMap de Envoy (`envoy-proxy-config`) llamando a `5.-envoy/01-configmap-envoy-create.sh`.
3. Configurar el `ServiceAccount` y los roles RBAC requeridos.
4. Aplicar los `Secrets` TLS generados desde `3.-certificates`.
5. Desplegar `client-app` y `server-app` con sus sidecars de Envoy e initContainers `proxy-init`.
6. Exponer los servicios y el ingress en el puerto `8443`.

### 3. Verificar el Estado

```bash
kubectl get pods,svc -n opa-ms
```

---

## 🧪 Pruebas de Autorización

### Petición sin token (Debe responder 403 Forbidden por OPA)

```bash
curl -k -i https://<INGRESS_IP_O_HOST>:8443/api/server/v1
# HTTP/1.1 403 Forbidden
```

### Generación de Tokens JWT con el Helper

Puedes generar tokens automáticamente con el helper integrado:

```bash
# Generar token para rol guest (válido):
make token

# Generar token para otro rol (ej. admin):
make token ROLE=admin

# Exportar token directo a una variable de entorno:
export TOKEN=$(make -s token-raw)

# Ejecutar suite de pruebas de autorización automáticas en vivo:
make test-auth
```

### Petición con JWT válido y rol `guest` (Permitido por OPA)

```bash
TOKEN=$(make -s token-raw)

curl -k -i https://<INGRESS_IP_O_HOST>:8443/api/server/v1 \
  -H "Authorization: Bearer $TOKEN"
# HTTP/1.1 200 OK
```

### Endpoints de salud y ping (Siempre permitidos sin autenticación)

```bash
curl -k -i https://<INGRESS_IP_O_HOST>:8443/health
curl -k -i https://<INGRESS_IP_O_HOST>:8443/
```

---

## 🧹 Limpieza

Para eliminar todos los recursos creados:

```bash
./7.-k8s-manifests/delete.sh
```