#!/usr/bin/env python3
"""
Automated OPA + Envoy Policy Authorization Tester
Executes live HTTP requests from inside the cluster (via client-app)
to verify that OPA and Envoy allow/deny traffic as expected.
"""

import subprocess
import sys


def get_token(role: str) -> str:
    out = subprocess.check_output(
        ["1.-core/jwt-token.py", "--role", role, "--raw"]
    )
    return out.decode("utf-8").strip()


def run_curl_in_pod(url: str, token: str = None) -> int:
    auth_header = f"headers={{'Authorization': 'Bearer {token}'}}" if token else "headers={}"
    code_snippet = (
        "import urllib.request, urllib.error, ssl\n"
        "ctx = ssl._create_unverified_context()\n"
        f"req = urllib.request.Request('{url}', {auth_header})\n"
        "try:\n"
        "    resp = urllib.request.urlopen(req, context=ctx)\n"
        "    print(resp.status)\n"
        "except urllib.error.HTTPError as e:\n"
        "    print(e.code)\n"
    )

    cmd = [
        "kubectl", "--context=kind-opa-cluster", "exec", "-n", "opa-ms",
        "-c", "client-app", "deployment/client-app",
        "--", "python", "-c", code_snippet
    ]
    try:
        res = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode("utf-8").strip()
        lines = [line for line in res.splitlines() if line.strip().isdigit()]
        if lines:
            return int(lines[-1])
        return int(res)
    except subprocess.CalledProcessError as err:
        print(f"Error executing in pod: {err.stderr.decode()}", file=sys.stderr)
        return -1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return -1


def main():
    green = "\033[0;32m"
    red = "\033[0;31m"
    cyan = "\033[0;36m"
    bold = "\033[1m"
    reset = "\033[0m"

    print(f"\n{cyan}{bold}=== OPA + Envoy Authorization Live Test Suite ==={reset}\n")

    guest_token = get_token("guest")
    admin_token = get_token("admin")

    server_base = "https://server-app.opa-ms.svc.cluster.local:8443"

    tests = [
        {
            "desc": "Health Check (No Token)",
            "url": f"{server_base}/health",
            "token": None,
            "expected": 200,
            "explanation": "Permitido libremente por regla: allow { glob.match('/health*', ...) }"
        },
        {
            "desc": "API /api/server/v1 (Sin Token)",
            "url": f"{server_base}/api/server/v1",
            "token": None,
            "expected": 403,
            "explanation": "Denegado por política: default allow = false (requiere JWT)"
        },
        {
            "desc": "API /api/server/v1 (Token con rol 'guest')",
            "url": f"{server_base}/api/server/v1",
            "token": guest_token,
            "expected": 200,
            "explanation": "Permitido por regla: action_allowed { token.payload.role == 'guest' }"
        },
        {
            "desc": "API /api/server/v1 (Token con rol 'admin')",
            "url": f"{server_base}/api/server/v1",
            "token": admin_token,
            "expected": 403,
            "explanation": "Denegado por política: el rol 'admin' no está autorizado en este endpoint"
        },
    ]

    passed = 0
    total = len(tests)

    for i, test in enumerate(tests, 1):
        status = run_curl_in_pod(test["url"], test["token"])
        is_pass = status == test["expected"]
        if is_pass:
            passed += 1
            badge = f"{green}[PASS - HTTP {status}]{reset}"
        else:
            badge = f"{red}[FAIL - Obtenido: {status}, Esperado: {test['expected']}]{reset}"

        print(f"  {i}. {test['desc']:<45} {badge}")
        print(f"     ↳ {test['explanation']}\n")

    print(f"{bold}Resultado final: {passed}/{total} pruebas exitosas.{reset}\n")
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
