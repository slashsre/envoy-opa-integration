#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/envoy-python-apps.yaml}"
CONFIG_MAP_NAME="${2:-envoy-proxy-config}"
NAMESPACE="${3:-opa-ms}"

echo "==> Creating Envoy ConfigMap ($CONFIG_MAP_NAME) from $CONFIG_FILE in $NAMESPACE..."
kubectl create configmap "$CONFIG_MAP_NAME" \
  --from-file="$CONFIG_FILE" \
  -n "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
