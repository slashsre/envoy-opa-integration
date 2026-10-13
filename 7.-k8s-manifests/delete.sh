#!/bin/bash
# -------------------------------------------------------------------
# Cleanup all resources for OPA + Envoy + Python microservices POC
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deleting Client App..."
kubectl delete -f "$SCRIPT_DIR/client-app-1.0.0/service.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/client-app-1.0.0/deployment.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/client-app-1.0.0/client-secret.yaml" --ignore-not-found

echo "==> Deleting Server App..."
kubectl delete -f "$SCRIPT_DIR/server-app-1.0.0/ingress.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/server-app-1.0.0/service.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/server-app-1.0.0/deployment.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/server-app-1.0.0/secret-tls.yaml" --ignore-not-found
kubectl delete -f "$SCRIPT_DIR/server-app-1.0.0/server-backend-ca.yaml" --ignore-not-found

echo "==> Deleting Envoy ConfigMap..."
kubectl delete configmap envoy-proxy-config -n opa-ms --ignore-not-found

echo "==> Deleting RBAC..."
kubectl delete -f "$SCRIPT_DIR/rbac.yaml" --ignore-not-found

echo "==> Deleting namespace..."
kubectl delete -f "$SCRIPT_DIR/namespace.yaml" --ignore-not-found

echo "==> Cleanup complete!"
