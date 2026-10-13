#!/bin/bash
# Prepare namespace, Envoy config, and secrets for microservices
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Preparing opa-ms namespace and configuration..."
kubectl apply -f "$ROOT_DIR/7.-k8s-manifests/namespace.yaml"

# Create Envoy ConfigMap
"$ROOT_DIR/5.-envoy/01-configmap-envoy-create.sh"

# Create ServiceAccount and RBAC
kubectl apply -f "$ROOT_DIR/7.-k8s-manifests/rbac.yaml"

# Apply TLS secrets
kubectl apply -f "$ROOT_DIR/7.-k8s-manifests/server-app-1.0.0/secret-tls.yaml"
kubectl apply -f "$ROOT_DIR/7.-k8s-manifests/client-app-1.0.0/client-secret.yaml"
