# 1. Imagen base minima y versionada explicitamente
FROM python:3.11-slim

# 2. Variables de entorno estandar
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

WORKDIR ${APP_HOME}

# 3. Crear usuario sin privilegios
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -d ${APP_HOME} appuser

# 4. Capa de dependencias optimizada para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar codigo fuente
COPY . .

# 6. Asignar permisos al usuario no-root
RUN chown -R appuser:appgroup ${APP_HOME}

# 7. Cambiar al usuario sin privilegios
USER 10001

# 8. Documentar puerto expuesto
EXPOSE 5000

# 9. Ejecucion como PID 1 (formato exec)
CMD ["python", "server.py"]