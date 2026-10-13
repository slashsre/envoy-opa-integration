# Guía de Contribución

¡Gracias por tu interés en contribuir a este proyecto de integración de **Open Policy Agent (OPA) + Envoy Proxy**!

## Flujo de Trabajo para Contribuir

1. **Haz un Fork** del repositorio en GitHub.
2. **Crea una rama descriptiva** para tu funcionalidad o corrección:
   ```bash
   git checkout -b feature/nueva-politica-rego
   ```
3. **Instala y valida localmente con KinD**:
   ```bash
   make install
   make test-auth
   ```
4. **Verifica que los tests pasen exitosamente**:
   - `make test-auth` debe reportar `4/4 pruebas exitosas`.
   - `make certs` debe validar la generación de certificados sin errores.
5. **Realiza tus commits con mensajes claros**:
   ```bash
   git commit -m "feat(rego): add support for role-based write operations"
   ```
6. **Envía un Pull Request** contra la rama `main` explicando los cambios realizados y los resultados de las pruebas.

## Estilo de Código y Buenas Prácticas
- **Rego**: Mantener las políticas modulares y bien comentadas en `6.-opa/regos/`.
- **Kubernetes**: Los manifiestos deben ubicarse en su carpeta numerada correspondiente (`7.-k8s-manifests/`).
- **Scripts**: Usar `set -euo pipefail` y paths dinámicos independientes del directorio de ejecución.
