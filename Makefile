# ============================================================================
# Makefile for OPA + Envoy Integration POC on KinD
# ============================================================================

.SHELLFLAGS := -euo pipefail -c
.DEFAULT_GOAL := help

# Cluster & Registry Variables
CLUSTER_NAME    ?= opa-cluster
REG_NAME        ?= kind-registry
REG_PORT        ?= 5000
KIND_CONFIG     ?= 2.-cluster/kind-configuration.yaml
COREDNS_CONFIG  ?= 2.-cluster/coredns-configmap.yaml
NAMESPACE       ?= opa-ms
OPA_NAMESPACE   ?= opa

# Application Image Tags (routed through the local KinD registry)
IMAGE_CLIENT_TAG ?= localhost:$(REG_PORT)/client-app:1.0.0
IMAGE_SERVER_TAG ?= localhost:$(REG_PORT)/server-app:1.0.0

.PHONY: help registry registry-stop cluster-up cluster-down cluster-status \
        ingress-controller build-images push-images images certs \
        deploy-opa delete-opa deploy-apps delete-apps install up \
        clean down dist-clean status logs-client logs-server logs-envoy-server logs-opa \
        token token-raw test-auth

# ----------------------------------------------------------------------------
# Help
# ----------------------------------------------------------------------------
help: ## Show this help message
	@1.-core/banner.sh
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ----------------------------------------------------------------------------
# Local container registry
# ----------------------------------------------------------------------------
registry: ## Start the local docker registry (kind-registry:5000)
	@if [ "$$(docker inspect -f '{{.State.Running}}' $(REG_NAME) 2>/dev/null || true)" != 'true' ]; then \
		echo ">> Starting registry $(REG_NAME) on 127.0.0.1:$(REG_PORT)"; \
		docker run -d --restart=always -p "127.0.0.1:$(REG_PORT):5000" \
			--network bridge --name $(REG_NAME) registry:3; \
	else \
		echo ">> Registry $(REG_NAME) already running"; \
	fi

registry-stop: ## Stop and remove the local container registry
	@if [ "$$(docker ps -aq -f name=^$(REG_NAME)$$)" ]; then \
		echo ">> Stopping and removing $(REG_NAME)..."; \
		docker rm -f $(REG_NAME) >/dev/null; \
	fi

# ----------------------------------------------------------------------------
# KinD Cluster Management (2.-cluster)
# ----------------------------------------------------------------------------
cluster-up: registry ## Create the KinD cluster with local registry and CoreDNS setup
	@if ! kind get clusters -q 2>/dev/null | grep -q "^$(CLUSTER_NAME)$$"; then \
		echo ">> Creating KinD cluster $(CLUSTER_NAME)..."; \
		kind create cluster --name $(CLUSTER_NAME) --config $(KIND_CONFIG); \
	else \
		echo ">> KinD cluster $(CLUSTER_NAME) already exists"; \
	fi
	@echo ">> Connecting registry $(REG_NAME) to KinD network..."
	@if [ "$$(docker inspect -f='{{json .NetworkSettings.Networks.kind}}' $(REG_NAME) 2>/dev/null)" = 'null' ]; then \
		docker network connect kind $(REG_NAME) 2>/dev/null || true; \
	fi
	@echo ">> Documenting local-registry-hosting in kube-public..."
	@printf '%s\n' \
		'apiVersion: v1' \
		'kind: ConfigMap' \
		'metadata:' \
		'  name: local-registry-hosting' \
		'  namespace: kube-public' \
		'data:' \
		'  localRegistryHosting.v1: |' \
		'    host: "localhost:$(REG_PORT)"' \
		'    help: "https://kind.sigs.k8s.io/docs/user/local-registry/"' \
		| kubectl apply -f - >/dev/null 2>&1 || true
	@echo ">> Applying CoreDNS configuration with service rewrites..."
	@kubectl -n kube-system apply -f $(COREDNS_CONFIG)
	@kubectl -n kube-system rollout restart deployment coredns

cluster-down: ## Delete the KinD cluster
	@echo ">> Deleting KinD cluster $(CLUSTER_NAME)..."
	@kind delete cluster --name $(CLUSTER_NAME)

cluster-status: ## Show cluster node and component status
	@kubectl get nodes -o wide
	@kubectl get pods -A

ingress-controller: ## Install Ingress NGINX controller for KinD
	@echo ">> Installing Ingress NGINX controller for KinD..."
	@kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	@echo ">> Waiting for Ingress controller to be ready (timeout 120s)..."
	@kubectl wait --namespace ingress-nginx \
		--for=condition=ready pod \
		--selector=app.kubernetes.io/component=controller \
		--timeout=120s 2>/dev/null || echo "Ingress controller deployment initiated."

# ----------------------------------------------------------------------------
# Application Images (4.-apps)
# ----------------------------------------------------------------------------
build-images: ## Build Docker images for client-app and server-app
	@echo ">> Building $(IMAGE_CLIENT_TAG)..."
	@docker build -t $(IMAGE_CLIENT_TAG) 4.-apps/client-app-1.0.0
	@echo ">> Building $(IMAGE_SERVER_TAG)..."
	@docker build -t $(IMAGE_SERVER_TAG) 4.-apps/server-app-1.0.0

push-images: ## Push images to local registry (localhost:5000)
	@echo ">> Pushing $(IMAGE_CLIENT_TAG)..."
	@docker push $(IMAGE_CLIENT_TAG)
	@echo ">> Pushing $(IMAGE_SERVER_TAG)..."
	@docker push $(IMAGE_SERVER_TAG)

images: build-images push-images ## Build and push all application images

# ----------------------------------------------------------------------------
# TLS Certificates (3.-certificates)
# ----------------------------------------------------------------------------
certs: ## Regenerate TLS certificates and update Kubernetes Secret manifests
	@echo ">> Regenerating TLS certificate and private key..."
	@3.-certificates/generate.sh
	@echo ">> Updating Kubernetes Secret manifests in 7.-k8s-manifests..."
	@python3 -c "import base64; \
crt = base64.b64encode(open('3.-certificates/server.crt','rb').read()).decode('utf-8'); \
key = base64.b64encode(open('3.-certificates/server.key','rb').read()).decode('utf-8'); \
open('7.-k8s-manifests/server-app-1.0.0/secret-tls.yaml','w').write(f'apiVersion: v1\ndata:\n  tls.crt: {crt}\n  tls.key: {key}\nkind: Secret\nmetadata:\n  name: server-tls-secret\n  namespace: $(NAMESPACE)\ntype: kubernetes.io/tls\n'); \
open('7.-k8s-manifests/server-app-1.0.0/server-backend-ca.yaml','w').write(f'apiVersion: v1\ndata:\n  ca.crt: {crt}\nkind: Secret\nmetadata:\n  name: server-backend-ca\n  namespace: $(NAMESPACE)\n'); \
open('7.-k8s-manifests/client-app-1.0.0/client-secret.yaml','w').write(f'apiVersion: v1\ndata:\n  server.crt: {crt}\nkind: Secret\nmetadata:\n  name: client-secret\n  namespace: $(NAMESPACE)\n');"
	@echo ">> Certificates and Secrets updated successfully."

# ----------------------------------------------------------------------------
# OPA Deployment (6.-opa)
# ----------------------------------------------------------------------------
deploy-opa: ## Deploy OPA engine with Envoy ext_authz plugin and Rego policies
	@6.-opa/opa-install.sh

delete-opa: ## Delete OPA resources and namespace
	@echo ">> Deleting OPA deployment..."
	@kubectl delete -f 6.-opa/opa-deployment.yaml -n $(OPA_NAMESPACE) --ignore-not-found
	@kubectl delete ns $(OPA_NAMESPACE) --ignore-not-found

# ----------------------------------------------------------------------------
# Python Microservices & Envoy Sidecars (7.-k8s-manifests)
# ----------------------------------------------------------------------------
deploy-apps: ## Deploy Python apps, Envoy sidecars, Secrets, and Services
	@7.-k8s-manifests/deploy.sh

delete-apps: ## Delete Python apps, Envoy ConfigMap, and opa-ms namespace
	@7.-k8s-manifests/delete.sh

# ----------------------------------------------------------------------------
# Full Lifecycle Workflows
# ----------------------------------------------------------------------------
install: cluster-up images deploy-opa deploy-apps ## Full setup: cluster + registry + images + OPA + apps
up: install ## Alias for install

clean: delete-apps delete-opa ## Cleanup applications and OPA from cluster
down: cluster-down ## Delete KinD cluster
dist-clean: clean cluster-down registry-stop ## Full cleanup: apps + OPA + cluster + registry

# ----------------------------------------------------------------------------
# Observation & Logs
# ----------------------------------------------------------------------------
status: ## Display all pods, services, and ingresses in opa-ms and opa
	@echo "=== [Namespace: $(NAMESPACE)] ==="
	@kubectl get pods,svc,ingress -n $(NAMESPACE) 2>/dev/null || true
	@echo ""
	@echo "=== [Namespace: $(OPA_NAMESPACE)] ==="
	@kubectl get pods,svc -n $(OPA_NAMESPACE) 2>/dev/null || true

logs-client: ## Tail client-app pod logs
	@kubectl logs -n $(NAMESPACE) -l app=client-app -c client-app -f

logs-server: ## Tail server-app pod logs
	@kubectl logs -n $(NAMESPACE) -l app=server-app -c server-app -f

logs-envoy-server: ## Tail server Envoy sidecar logs
	@kubectl logs -n $(NAMESPACE) -l app=server-app -c envoy -f

logs-opa: ## Tail OPA decision logs
	@kubectl logs -n $(OPA_NAMESPACE) -l app=opa -c opa -f

# ----------------------------------------------------------------------------
# JWT Helpers & Policy Testing (1.-core)
# ----------------------------------------------------------------------------
ROLE     ?= guest
JWT_USER ?= developer

token: ## Generate JWT token for testing (make token [ROLE=guest|admin] [JWT_USER=name])
	@1.-core/jwt-token.py --role $(ROLE) --user $(JWT_USER)

token-raw: ## Print only the raw JWT string
	@1.-core/jwt-token.py --role $(ROLE) --user $(JWT_USER) --raw

test-auth: ## Run automated live OPA + Envoy authorization test suite
	@1.-core/test-auth.py

