# Referencias y Especificaciones del Proyecto

Este documento recopila las referencias oficiales, especificaciones técnicas y estándares de la industria que sustentan la arquitectura de **OPA + Envoy Proxy Integration**.

---

## 1. Open Policy Agent (OPA)
- **Documentación Oficial**: [Open Policy Agent Docs](https://www.openpolicyagent.org/docs/latest/)
- **Integración OPA + Envoy (`ext_authz`)**: [OPA Envoy Introduction](https://www.openpolicyagent.org/docs/latest/envoy-introduction/)
- **Referencia del Lenguaje Rego**: [Rego Policy Language](https://www.openpolicyagent.org/docs/latest/policy-language/)
- **Librería Criptográfica y JWT en OPA (`io.jwt.*`)**: [OPA Built-in Functions - JWT](https://www.openpolicyagent.org/docs/latest/policy-reference/#json-web-tokens)
- **Repositorio de Integración Envoy**: [open-policy-agent/opa-envoy-plugin](https://github.com/open-policy-agent/opa-envoy-plugin)

---

## 2. Envoy Proxy
- **Documentación Oficial**: [Envoy Proxy Architecture & Guides](https://www.envoyproxy.io/docs/envoy/latest/)
- **Filtro de Autorización Externa (`envoy.filters.http.ext_authz`)**: [Envoy External Authorization HTTP Filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_authz_filter)
- **Filtro de Gestión de Conexiones HTTP**: [HttpConnectionManager](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/http_conn_man)
- **Configuración de TLS / SSL (Transport Sockets)**: [Envoy TLS Configuration](https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/tls/v3/tls.proto)
- **Envoy gRPC Ext-Authz Service Proto**: [pb.ext_authz.v3](https://github.com/envoyproxy/envoy/blob/main/api/envoy/service/auth/v3/external_auth.proto)

---

## 3. Estándares de Autenticación y Criptografía
- **RFC 7519**: [JSON Web Token (JWT)](https://datatracker.ietf.org/doc/html/rfc7519) — Definición y claims estándar (`sub`, `iss`, `exp`, `iat`, `role`).
- **RFC 7515**: [JSON Web Signature (JWS)](https://datatracker.ietf.org/doc/html/rfc7515) — Algoritmo HMAC-SHA256 (`HS256`).
- **RFC 5280**: [Internet X.509 Public Key Infrastructure Certificate and CRL Profile](https://datatracker.ietf.org/doc/html/rfc5280) — Especificación de Subject Alternative Names (SAN) para mTLS y DNS en clusters K8s.
- **Herramienta de depuración JWT**: [JWT.io](https://jwt.io/)

---

## 4. Kubernetes y Ecosistema Cloud Native
- **Documentación de Kubernetes**: [Kubernetes Documentation](https://kubernetes.io/docs/)
- **KinD (Kubernetes in Docker)**: [KinD Documentation](https://kind.sigs.k8s.io/)
- **KinD Local Container Registry Pattern**: [KinD Local Registry](https://kind.sigs.k8s.io/docs/user/local-registry/)
- **CoreDNS Plugin Rewrite**: [CoreDNS Rewrite Plugin Documentation](https://coredns.io/plugins/rewrite/)
- **Kubernetes Pod Security Standards (PSS)**: [Pod Security Standards - Restricted Profile](https://kubernetes.io/docs/concepts/security/pod-security-standards/)

---

## 5. Patrones de Diseño y Seguridad Zero Trust
- **NIST SP 800-207**: [Zero Trust Architecture](https://csrc.nist.gov/publications/detail/sp/800-207/final)
- **Sidecar Pattern**: [Cloud Native Sidecar Architecture (Envoy Sidecars)](https://kubernetes.io/docs/concepts/workloads/pods/#how-pods-manage-multiple-containers)
- **Policy as Code (PaC)**: Desacoplamiento entre la lógica de negocio (Python Flask) y las políticas de autorización (Rego + OPA).
