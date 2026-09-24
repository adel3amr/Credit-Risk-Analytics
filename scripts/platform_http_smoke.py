"""Actual server startup/HTTP check; not a substitute for browser testing."""

import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from credit_platform.common import ROOT, atomic_json

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
p = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "credit_platform.api:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-access-log",
    ],
    cwd=ROOT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
try:
    for attempt in range(50):
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health/ready", timeout=1
            ) as response:
                result = {
                    "status_code": response.status,
                    "body": json.loads(response.read()),
                    "actual_socket_http": True,
                }
            break
        except Exception:
            if p.poll() is not None:
                raise RuntimeError("Server exited during startup")
            time.sleep(0.2)
    else:
        raise RuntimeError("Readiness timeout")
    for path in ("/", "/static/app.js", "/static/style.css", "/openapi.json"):
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}{path}", timeout=3
        ) as response:
            assert response.status == 200
    atomic_json(ROOT / "platform_evidence/http_startup.json", result)
    print(result)
finally:
    p.terminate()
    try:
        p.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
