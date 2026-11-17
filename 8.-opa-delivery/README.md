# 8.- OPA Delivery (pipelines consumidores)

Este repo **no** contiene la lógica de despliegue de las políticas OPA. Esa lógica (CLI, política
genérica, `data.json` con los endpoints, Kustomize de OPA, Flux) vive en el repo
[**slashsre/opa-delivery-k8s**](https://github.com/slashsre/opa-delivery-k8s). Aquí solo están los pipelines que hacen checkout de ese repo y lo ejecutan:

| Archivo | CI |
|---------|----|
| [`Jenkinsfile`](Jenkinsfile) | Jenkins (Script Path `8.-opa-delivery/Jenkinsfile`) |
| [`../.github/workflows/opa-delivery.yml`](../.github/workflows/opa-delivery.yml) | GitHub Actions (*Run workflow*) |

```
envoy-opa-integration (este repo)          opa-delivery-k8s
┌─────────────────────────────┐  checkout  ┌──────────────────────────────────────┐
│ Jenkinsfile / workflow      │ ─────────▶ │ scripts/apply-change.sh  (cambio)    │
│ parámetros: OPERATION,      │            │ make test                (gate)      │
│ CALLER, ENDPOINT_PATH,      │            │ scripts/publish-change.sh            │
│ METHODS, DELIVERY_MODE      │            │   gitops   → PR → Flux               │
└─────────────────────────────┘            │   pipeline → push + kubectl apply    │
                                           └──────────────────────────────────────┘
```

Ejemplo: dar acceso `GET` a `/api/server/v1` al rol `admin` (token de `make token ROLE=admin`):

| Parámetro | Valor |
|-----------|-------|
| `OPERATION` | `add-endpoint` |
| `CALLER` | `admin` |
| `ENDPOINT_PATH` | `/api/server/v1` |
| `METHODS` | `GET` |
| `DELIVERY_MODE` | `gitops` o `pipeline` |

Después: `make test-auth` y la prueba con `ROLE=admin` (ver `TESTING.md` del repo delivery).

> Cuando OPA lo gestiona el delivery, **no** uses `make deploy-opa` ni `6.-opa/` de este repo:
> despliegan la versión anterior (con kube-mgmt) sobre el mismo namespace `opa`. Los
> microservicios (`make deploy-apps`) no cambian: Envoy sigue apuntando a
> `opa.opa.svc.cluster.local:9191`.
