#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Deploying OPA engine..."
kubectl create ns opa --dry-run=client -o yaml | kubectl apply -f -

# ConfigMap with Rego policies (read by kube-mgmt)
kubectl -n opa create configmap opa-policy \
  --from-file="$SCRIPT_DIR/regos/policy.rego" \
  --dry-run=client -o yaml | kubectl apply -f -

# Secret configuration
kubectl -n opa create secret generic opa-config \
  --from-file="$SCRIPT_DIR/opa-config.yaml" \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy OPA server and kube-mgmt
kubectl apply -f "$SCRIPT_DIR/opa-deployment.yaml" -n opa
