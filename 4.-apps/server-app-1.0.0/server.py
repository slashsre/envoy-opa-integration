import base64
import json
import logging
import os
import ssl
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from werkzeug.serving import run_simple, WSGIRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('server-service')

app = Flask(__name__)


def find_cert_paths():
    """Finds certificate and key paths checking env vars and known locations (including 3.-certificates)."""
    cert_env = os.getenv('CERT_PATH')
    key_env = os.getenv('KEY_PATH')

    candidate_cert_paths = [cert_env] if cert_env else []
    candidate_cert_paths += [
        'certs/server.crt',
        '/certs/server.crt',
        '3.-certificates/server.crt',
        '../../3.-certificates/server.crt',
        '../3.-certificates/server.crt',
    ]

    candidate_key_paths = [key_env] if key_env else []
    candidate_key_paths += [
        'certs/server.key',
        '/certs/server.key',
        '3.-certificates/server.key',
        '../../3.-certificates/server.key',
        '../3.-certificates/server.key',
    ]

    found_cert = next((p for p in candidate_cert_paths if p and os.path.exists(p)), None)
    found_key = next((p for p in candidate_key_paths if p and os.path.exists(p)), None)
    return found_cert, found_key


def parse_jwt_payload(auth_header):
    """Safely extracts and decodes the JWT payload from an Authorization header without external dependencies."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    try:
        token = auth_header.split(' ', 1)[1].strip()
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            rem = len(payload_b64) % 4
            if rem:
                payload_b64 += '=' * (4 - rem)
            decoded = base64.urlsafe_b64decode(payload_b64.encode('utf-8'))
            return json.loads(decoded.decode('utf-8'))
    except Exception as exc:
        logger.debug(f'Could not parse JWT payload: {exc}')
    return None


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'server-service',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/server/v1',
            'health': '/health'
        }
    }), 200


@app.route('/health', methods=['GET'])
@app.route('/healthz', methods=['GET'])
def health():
    return jsonify({
        'status': 'UP',
        'service': 'server-service',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@app.route('/api/server/v1', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_server_v1():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    auth_header = request.headers.get('Authorization')
    jwt_payload = parse_jwt_payload(auth_header)

    # Filter relevant headers for visibility
    relevant_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() in (
            'authorization', 'x-forwarded-for', 'x-request-id',
            'user-agent', 'content-type', 'host', 'x-envoy-external-address'
        )
    }

    body = request.get_json(silent=True)

    response_data = {
        'status': 'success',
        'service': 'server-service',
        'version': 'v1',
        'endpoint': '/api/server/v1',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'method': request.method,
        'client_ip': client_ip,
        'host': request.host,
        'headers': relevant_headers,
        'jwt_payload': jwt_payload,
        'received_body': body,
        'message': 'Hello from OPA Server Microservice!'
    }

    logger.info(f"[{request.method}] /api/server/v1 from {client_ip} (Host: {request.host})")
    return jsonify(response_data), 200


if __name__ == '__main__':
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT') or os.getenv('CONTAINER_SERVICE_PORT') or os.getenv('SERVER_PORT', '5000'))
    ssl_env_str = os.getenv('SSL', '').lower()

    cert_path, key_path = find_cert_paths()

    # Determine TLS activation
    if ssl_env_str in ('false', 'no', '0'):
        use_tls = False
    elif ssl_env_str in ('true', 'yes', '1'):
        use_tls = True
    else:
        # Default: auto-enable TLS if certificates from 3.-certificates or certs/ are detected
        use_tls = bool(cert_path and key_path)

    if use_tls:
        if cert_path and key_path:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(cert_path, key_path)
            logger.info(f'Starting HTTPS server on {host}:{port} using cert: {cert_path} and key: {key_path}...')
            run_simple(host, port, app, request_handler=WSGIRequestHandler, ssl_context=ctx)
        else:
            logger.warning('SSL was requested but certificate files were not found. Falling back to HTTP.')
            logger.info(f'Starting HTTP server on {host}:{port}...')
            run_simple(host, port, app, request_handler=WSGIRequestHandler)
    else:
        logger.info(f'Starting HTTP server on {host}:{port} (TLS disabled)...')
        run_simple(host, port, app, request_handler=WSGIRequestHandler)
