import base64
import json
import logging
import os
import ssl
import threading
import time
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, request
from werkzeug.serving import run_simple, WSGIRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger('client-service')

app = Flask(__name__)

# Outgoing session
_http_session = requests.Session()


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


def _get_ssl_verify():
    """Determine SSL verification strategy for outgoing requests."""
    insecure = os.getenv('INSECURE_SKIP_VERIFY', 'false').lower() in ('true', 'yes', '1')
    if insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return False

    ca_env = os.getenv('CA_CERT_PATH') or os.getenv('CERT_PATH')
    candidate_ca_paths = [ca_env] if ca_env else []
    candidate_ca_paths += [
        'certs/server.crt',
        '/certs/server.crt',
        '3.-certificates/server.crt',
        '../../3.-certificates/server.crt',
        '../3.-certificates/server.crt',
    ]
    found_ca = next((p for p in candidate_ca_paths if p and os.path.exists(p)), None)
    if found_ca:
        return found_ca

    verify_env = os.getenv('VERIFY_SSL', 'true').lower() in ('true', 'yes', '1')
    return verify_env


def _make_upstream_request(target_url, headers=None, timeout=5):
    """Executes an upstream HTTP call and returns structured details."""
    req_headers = {
        'User-Agent': 'client-service/1.0.0',
        'X-Forwarded-By': 'client-service'
    }
    if headers:
        req_headers.update(headers)

    verify = _get_ssl_verify()
    start_time = time.time()
    try:
        resp = _http_session.get(target_url, headers=req_headers, timeout=timeout, verify=verify)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        return {
            'target_url': target_url,
            'status_code': resp.status_code,
            'duration_ms': elapsed_ms,
            'response': body
        }, None
    except Exception as exc:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f'Error calling upstream {target_url}: {exc}')
        return {
            'target_url': target_url,
            'duration_ms': elapsed_ms,
            'error': str(exc)
        }, exc


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'client-service',
        'version': '1.0.0',
        'endpoints': {
            'api': '/api/client/v1',
            'health': '/health'
        }
    }), 200


@app.route('/health', methods=['GET'])
@app.route('/healthz', methods=['GET'])
def health():
    return jsonify({
        'status': 'UP',
        'service': 'client-service',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@app.route('/api/client/v1', methods=['GET', 'POST'])
def api_client_v1():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Determine target URL: query param -> json body -> env var
    body_json = request.get_json(silent=True) or {}
    target_url = (
        request.args.get('target') or
        body_json.get('target') or
        os.getenv('TARGET_URL') or
        os.getenv('SERVER_URL')
    )

    upstream_data = None
    status_code = 200
    overall_status = 'success'

    # If target_url is defined or provided, invoke upstream server
    if target_url:
        forward_headers = {}
        # Forward Authorization header if provided, or use configured token
        auth_header = request.headers.get('Authorization') or os.getenv('DEFAULT_AUTH_TOKEN')
        if auth_header:
            if not auth_header.startswith('Bearer ') and not auth_header.startswith('Basic '):
                auth_header = f'Bearer {auth_header}'
            forward_headers['Authorization'] = auth_header

        timeout = float(os.getenv('REQUEST_TIMEOUT', '5'))
        upstream_data, err = _make_upstream_request(target_url, headers=forward_headers, timeout=timeout)
        if err:
            overall_status = 'upstream_error'
            status_code = 502

    response_payload = {
        'status': overall_status,
        'service': 'client-service',
        'version': 'v1',
        'endpoint': '/api/client/v1',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'client_ip': client_ip,
        'host': request.host,
        'upstream_call': upstream_data,
        'message': 'Hello from OPA Client Microservice!'
    }

    logger.info(f"[{request.method}] /api/client/v1 called from {client_ip} -> upstream: {target_url or 'none'}")
    return jsonify(response_payload), status_code


def _background_loop(target_url, interval, timeout):
    """Optional background worker to periodically generate traffic for demo/testing."""
    logger.info(f'Starting background client loop to {target_url} (interval={interval}s)...')
    while True:
        try:
            auth = os.getenv('DEFAULT_AUTH_TOKEN')
            headers = {'Authorization': f'Bearer {auth}'} if auth else None
            data, err = _make_upstream_request(target_url, headers=headers, timeout=timeout)
            if err:
                logger.warning(f'[auto-client] Request to {target_url} failed: {err}')
            else:
                logger.info(f"[auto-client] Request to {target_url} -> HTTP {data.get('status_code')}")
        except Exception as exc:
            logger.error(f'[auto-client] Unexpected error: {exc}')
        time.sleep(interval)


if __name__ == '__main__':
    host = os.getenv('SERVER_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT') or os.getenv('CONTAINER_SERVICE_PORT') or os.getenv('SERVER_PORT', '5000'))
    ssl_env_str = os.getenv('SSL', '').lower()

    cert_path, key_path = find_cert_paths()

    # Optional background loop for automated testing
    run_loop = os.getenv('RUN_BACKGROUND_LOOP', 'false').lower() in ('true', 'yes', '1')
    target_env = os.getenv('TARGET_URL') or os.getenv('SERVER_URL')
    interval_env = int(os.getenv('REQUEST_INTERVAL', '5'))
    timeout_env = float(os.getenv('REQUEST_TIMEOUT', '5'))

    if run_loop and target_env:
        loop_thread = threading.Thread(
            target=_background_loop,
            args=(target_env, interval_env, timeout_env),
            daemon=True
        )
        loop_thread.start()

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
            logger.info(f'Starting HTTPS client-service on {host}:{port} using cert: {cert_path} and key: {key_path}...')
            run_simple(host, port, app, request_handler=WSGIRequestHandler, ssl_context=ctx)
        else:
            logger.warning('SSL was requested but certificate files were not found. Falling back to HTTP.')
            logger.info(f'Starting HTTP client-service on {host}:{port}...')
            run_simple(host, port, app, request_handler=WSGIRequestHandler)
    else:
        logger.info(f'Starting HTTP client-service on {host}:{port} (TLS disabled)...')
        run_simple(host, port, app, request_handler=WSGIRequestHandler)