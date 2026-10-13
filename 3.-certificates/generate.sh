#!/bin/bash
# -------------------------------------------------------------------
# Generate TLS certificates with SAN extensions for opa-ms microservices
# -------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Generating TLS private key and certificate..."
openssl req -x509 -nodes -days 730 -newkey rsa:2048 \
  -keyout "$SCRIPT_DIR/server.key" \
  -out "$SCRIPT_DIR/server.crt" \
  -config "$SCRIPT_DIR/san.cnf" \
  -extensions v3_ca

echo ""
echo "==> Certificate generated successfully:"
openssl x509 -in "$SCRIPT_DIR/server.crt" -text -noout | grep -E "Subject:|Issuer:|Not After|DNS:"
