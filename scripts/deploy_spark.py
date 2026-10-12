"""Deploy the demo to the Spark k3s cluster: Secret from .env (values never printed), then k8s/app.yaml.

    python3 scripts/deploy_spark.py
The DNS record is separate: HOST_LABEL=agenticai-compressor <mtvlab>/agenticai/global-bank-dns.sh
"""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CTX = ["--context", "spark-k3s"]  # the default context is another cluster
KEYS = ["AMD_VLLM_BASE_URL", "AMD_VLLM_API_KEY", "AMD_VLLM_MODEL", "EVOLUS_API_KEY", "EVOLUS_APP_ID"]

vals = {}
for line in (ROOT / ".env").read_text().splitlines():
    s = line.strip()
    if s and not s.startswith("#") and "=" in s:
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip()
missing = [k for k in KEYS if not vals.get(k)]
if missing:
    raise SystemExit(f"missing in .env: {missing}")

kubectl = lambda *a, **kw: subprocess.run(["kubectl", *CTX, *a], check=True, **kw)
kubectl("apply", "-f", str(ROOT / "k8s/app.yaml"))
secret = {"apiVersion": "v1", "kind": "Secret", "type": "Opaque",
          "metadata": {"name": "compressor-copilot-env", "namespace": "compressor-copilot"},
          "stringData": {k: vals[k] for k in KEYS}}
kubectl("apply", "-f", "-", input=json.dumps(secret), text=True)
kubectl("-n", "compressor-copilot", "rollout", "restart", "deployment/compressor-copilot")
print("applied; watch: kubectl --context spark-k3s -n compressor-copilot rollout status deploy/compressor-copilot")
