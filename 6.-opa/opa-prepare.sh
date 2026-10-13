#!/bin/bash
set -euo pipefail

# Create opa-ms namespace
kubectl create ns opa-ms --dry-run=client -o yaml | kubectl apply -f -

# Create opa namespace
kubectl create ns opa --dry-run=client -o yaml | kubectl apply -f -

# Create service account for OPA
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sa-opa-poc
  namespace: opa
EOF

# Apply cluster role binding to opa service account
OPA_SA=$(kubectl get sa -n opa --output=jsonpath='{.items..metadata.name}' 2>/dev/null | grep -o sa-opa-poc || true)
if [ -z "${OPA_SA}" ]; then
  kubectl create clusterrolebinding opa-admin-binding \
      --clusterrole cluster-admin \
      --serviceaccount opa:sa-opa-poc \
      --namespace opa
else
  echo "Service account ${OPA_SA} as cluster-admin already configured."
fi
