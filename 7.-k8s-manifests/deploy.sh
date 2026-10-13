#!/bin/bash
# -------------------------------------------------------------------
# Deploy all resources for OPA + Envoy + Python microservices POC
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Creating namespace..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"

echo "==> Creating Envoy ConfigMap..."
"$ROOT_DIR/5.-envoy/01-configmap-envoy-create.sh"

echo "==> Creating ServiceAccount and RBAC..."
kubectl apply -f "$SCRIPT_DIR/rbac.yaml"

echo "==> Deploying TLS secrets..."
kubectl apply -f "$SCRIPT_DIR/server-app-1.0.0/secret-tls.yaml"
kubectl apply -f "$SCRIPT_DIR/client-app-1.0.0/client-secret.yaml"

echo "==> Deploying Client App (client-app + envoy sidecar)..."
kubectl apply -f "$SCRIPT_DIR/client-app-1.0.0/deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/client-app-1.0.0/service.yaml"

echo "==> Deploying Server App (server-app + envoy sidecar)..."
kubectl apply -f "$SCRIPT_DIR/server-app-1.0.0/deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/server-app-1.0.0/service.yaml"
kubectl apply -f "$SCRIPT_DIR/server-app-1.0.0/ingress.yaml"
kubectl apply -f "$SCRIPT_DIR/server-app-1.0.0/server-backend-ca.yaml"

echo ""
echo "==> Deploy complete!"
echo "    Namespace:  opa-ms"
echo "    Services:   client-app (:8443), server-app (:8443)"
echo "    Ingress:    server-app-ingress"
echo ""
echo "    Verify with:"
echo "      kubectl get pods -n opa-ms"
echo "      kubectl get svc -n opa-ms"