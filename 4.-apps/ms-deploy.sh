#!/bin/bash
# Deploy microservices for OPA + Envoy POC
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "==> Deploying microservices with Envoy sidecars..."
"$ROOT_DIR/7.-k8s-manifests/deploy.sh"
