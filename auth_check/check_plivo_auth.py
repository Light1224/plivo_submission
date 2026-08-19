#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import ssl
import sys
import urllib.error
import urllib.request


def check_auth(auth_id: str, auth_token: str) -> tuple[int, str]:
    url = f"https://api.plivo.com/v1/Account/{auth_id}/"
    credentials = f"{auth_id}:{auth_token}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("ascii")

    req = urllib.request.Request(url=url, method="GET")
    req.add_header("Authorization", f"Basic {encoded}")

    context = ssl.create_default_context()

    try:
        with urllib.request.urlopen(req, context=context, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quick Plivo auth check via GET /v1/Account/{auth_id}/ (BasicAuth)."
    )
    parser.add_argument("--auth-id", required=True)
    parser.add_argument("--auth-token", required=True)
    args = parser.parse_args()

    status, body = check_auth(args.auth_id.strip(), args.auth_token.strip())

    print(f"HTTP {status}")
    try:
        parsed = json.loads(body)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(body)

    if status == 200:
        print("\nAuth check: SUCCESS")
        return 0

    if status == 401:
        print("\nAuth check: FAILED (401 Unauthorized)")
        return 2

    print("\nAuth check: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
