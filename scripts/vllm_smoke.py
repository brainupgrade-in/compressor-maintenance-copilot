"""Smoke test for the AMD-hosted vLLM endpoint. Stdlib only.

    python3 scripts/vllm_smoke.py            # uses .env
Exit 0 = endpoint answered a chat completion. Never prints secret values.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path


def load_env(path=Path(__file__).resolve().parent.parent / ".env"):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def main():
    load_env()
    base = os.environ.get("AMD_VLLM_BASE_URL", "").rstrip("/")
    key = os.environ.get("AMD_VLLM_API_KEY") or "EMPTY"
    if not base or "<" in base:
        sys.exit("FAIL: set AMD_VLLM_BASE_URL in .env")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    req = urllib.request.Request(f"{base}/models", headers=headers)
    models = [m["id"] for m in json.load(urllib.request.urlopen(req, timeout=15))["data"]]
    model = os.environ.get("AMD_VLLM_MODEL") or models[0]
    print(f"models served: {models}")

    body = json.dumps({"model": model, "max_tokens": 32,
                       "messages": [{"role": "user", "content": "Reply with exactly: AMD OK"}]}).encode()
    t0 = time.time()
    req = urllib.request.Request(f"{base}/chat/completions", data=body, headers=headers)
    out = json.load(urllib.request.urlopen(req, timeout=120))
    text = out["choices"][0]["message"]["content"]
    print(f"model={model} latency={time.time() - t0:.2f}s tokens={out.get('usage', {})}")
    print(f"reply: {text!r}")
    print("PASS" if text.strip() else "FAIL: empty reply")
    sys.exit(0 if text.strip() else 1)


if __name__ == "__main__":
    main()
