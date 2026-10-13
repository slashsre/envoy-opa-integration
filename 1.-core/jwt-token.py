#!/usr/bin/env python3
"""
JWT Token Generator for OPA + Envoy Integration POC
Generates HS256 JWT tokens compatible with OPA ext_authz Rego policy.
Uses only standard Python libraries (no pip dependencies required).
"""

import argparse
import base64
import hashlib
import hmac
import json
import time


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def generate_jwt(role: str = "guest", user: str = "developer", secret: str = "secret", exp_hours: int = 24) -> str:
    header = {
        "typ": "JWT",
        "alg": "HS256"
    }

    now = int(time.time())
    payload = {
        "sub": user,
        "user": user,
        "role": role,
        "iat": now,
        "exp": now + (exp_hours * 3600),
        "iss": "opa-envoy-poc"
    }

    encoded_header = base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_signature = base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def main():
    parser = argparse.ArgumentParser(description="Generate JWT tokens for OPA + Envoy POC")
    parser.add_argument("--role", default="guest", help="User role (e.g., guest, admin, viewer). Default: guest")
    parser.add_argument("--user", default="developer", help="Username for sub/user claims. Default: developer")
    parser.add_argument("--secret", default="secret", help="HMAC secret key. Default: secret")
    parser.add_argument("--exp", type=int, default=24, help="Expiration in hours. Default: 24")
    parser.add_argument("--raw", action="store_true", help="Print only the raw JWT string")

    args = parser.parse_args()
    token = generate_jwt(role=args.role, user=args.user, secret=args.secret, exp_hours=args.exp)

    if args.raw:
        print(token)
        return

    cyan = "\033[0;36m"
    green = "\033[0;32m"
    yellow = "\033[0;33m"
    bold = "\033[1m"
    reset = "\033[0m"

    print(f"\n{cyan}{bold}=== JWT Token Generator for OPA + Envoy ==={reset}")
    print(f"Role:      {green}{args.role}{reset} ({'ALLOWED by policy' if args.role == 'guest' else 'DENIED by policy'})")
    print(f"User:      {args.user}")
    print(f"Algorithm: HS256 (Secret: '{args.secret}')\n")

    print(f"{bold}Token:{reset}")
    print(f"{yellow}{token}{reset}\n")

    print(f"{bold}Usage examples:{reset}")
    print(f"  # Export as environment variable:")
    print(f"  export TOKEN=\"{token}\"\n")
    print(f"  # Test inside cluster via client-app:")
    print(f"  kubectl exec -n opa-ms -c client-app deployment/client-app -- python -c \"import urllib.request, ssl; ctx = ssl._create_unverified_context(); req = urllib.request.Request('https://server-app.opa-ms.svc.cluster.local:8443/api/server/v1', headers={{'Authorization': 'Bearer {token}'}}); print(urllib.request.urlopen(req, context=ctx).read().decode())\"")
    print()


if __name__ == "__main__":
    main()
