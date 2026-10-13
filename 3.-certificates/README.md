# 3.-certificates

Este directorio almacena los certificados X.509 y la clave privada TLS utilizados para la comunicación segura (HTTPS / mTLS) entre los microservicios en Python (`client-app` y `server-app`) y con **Envoy Proxy**.

---

## 📄 Contenido del Directorio

* **`san.cnf`**: Archivo de configuración OpenSSL con extensiones SAN (*Subject Alternative Name*) y capacidad de CA básica (`CA:TRUE`).
* **`server.crt`**: Certificado X.509 autofirmado válido hasta Septiembre de 2028.
* **`server.key`**: Clave privada RSA de 2048 bits correspondiente al certificado.

---

## 🌐 Dominios y Nombres Alternativos (SAN) Soportados

Configurados en [`san.cnf`](san.cnf):
* `DNS.1 = server`
* `DNS.2 = server.example.com`
* `DNS.3 = server.local`
* `DNS.4 = localhost`
* `DNS.5 = server.opa-ms.svc.cluster.local`
* `DNS.6 = server-app`
* `DNS.7 = server-app.opa-ms`
* `DNS.8 = server-app.opa-ms.svc.cluster.local`
* `DNS.9 = client-app`
* `DNS.10 = client-app.opa-ms`
* `DNS.11 = client-app.opa-ms.svc.cluster.local`
* `IP.1  = 127.0.0.1`

---

## 🔄 Cómo Regenerar los Certificados (Opcional)

Si necesitas emitir un nuevo certificado con fechas extendidas o dominios adicionales:

```bash
openssl req -x509 -nodes -days 730 -newkey rsa:2048 \
  -keyout 3.-certificates/server.key \
  -out 3.-certificates/server.crt \
  -config 3.-certificates/san.cnf \
  -extensions v3_ca
```

---

## ☸️ Despliegue en Kubernetes (Secret)

Para que los pods en Kubernetes puedan montar estos certificados en sus contenedores (tanto la app Python como el sidecar de Envoy):

```bash
# Crear el Secret server-tls-secret en el namespace opa-ms
kubectl create secret tls server-tls-secret \
  --cert=3.-certificates/server.crt \
  --key=3.-certificates/server.key \
  -n opa-ms
```

---

## 🐍 Integración con los Microservicios Python

Los servicios [`server.py`](../4.-apps/server-app-1.0.0/server.py) y [`client.py`](../4.-apps/client-app-1.0.0/client.py) detectan automáticamente estos certificados si están en esta carpeta o montados en `certs/`:

1. **`server-app`**:
   * Usa `server.crt` y `server.key` para levantar el listener HTTPS.
2. **`client-app`**:
   * Utiliza `server.crt` como CA bundle confiable (`verify='3.-certificates/server.crt'`) al realizar peticiones HTTPS hacia el servidor.
