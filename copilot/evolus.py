"""Evolus building blocks: a knowledge library, an agent on our AMD-hosted model, and a workflow.

`python -m copilot.evolus setup` creates them once over the REST API and saves their ids to evolus.json.
`workflow_llm` and `agent_llm` have the same signature as agent.call_llm, so explain() and chat() run
through Evolus while the guardrails in agent.py still check every answer.
"""
import json
import os
import sys
import time

import requests

from .agent import load_env
from .data import ROOT
from .kb import load_docs

API = "https://api.evolus.ai/api/v1"
IDS = ROOT / "evolus.json"
MODEL_KEY = "own/DeepSeek-V4-Flash"  # our Token Factory connection, so the agent thinks on AMD GPUs
AGENT_PROMPT = (
    "You are the maintenance copilot for an industrial air compressor (APU-300). "
    "Your library holds the compressor manual and past work orders; each file starts with its citation id. "
    "Follow the instructions and the answer format given in each request exactly. "
    "Answer directly: do not describe your searching or what you are about to do.")


def _headers(user: bool = False) -> dict:
    load_env()
    key = {"X-User-ApiKey": os.environ["EVOLUS_USER_API_KEY"]} if user else {"X-ApiKey": os.environ["EVOLUS_API_KEY"]}
    return {**key, "X-Application-Id": os.environ["EVOLUS_APP_ID"]}


def _call(method: str, path: str, user: bool = False, **kw):
    r = requests.request(method, API + path, headers=_headers(user), timeout=kw.pop("timeout", 60), **kw)
    if not r.ok:
        raise RuntimeError(f"Evolus {method} {path}: {r.status_code} {r.text[:300]}")
    return r.json() if r.content else None


def ids() -> dict:
    return json.loads(IDS.read_text()) if IDS.exists() else {}


def setup() -> dict:
    """Create the library, agent and workflow (skips any that evolus.json already records)."""
    load_env()
    out = ids()
    if "agent" not in out:
        out["agent"] = _call("POST", "/agents", json={
            "name": "Compressor Maintenance Copilot", "prompt": AGENT_PROMPT, "language": "en",
            "modelKey": MODEL_KEY, "isChatVisible": True})["agentId"]
        IDS.write_text(json.dumps(out, indent=1) + "\n")
    if "library" not in out and os.environ.get("EVOLUS_USER_API_KEY"):
        # Library calls need a personal user key; the app key gets 401. Reuse one left by a failed run.
        lib = next((m for m in _call("GET", "/memories", user=True) if m["name"] == "Compressor KB"), None)
        lib = lib or _call("POST", "/memories/simple", user=True, json={"name": "Compressor KB"})
        out["library"] = lib["id"]
        IDS.write_text(json.dumps(out, indent=1) + "\n")
        _call("POST", f"/agents/{out['agent']}/memories", user=True, json={"memoryId": out["library"]})
        have = {d["title"] for d in _call(
            "GET", f"/memories/{out['library']}/documents", user=True)}
        for d in load_docs():
            name = d.id.replace("#", "-") + ".md"
            if name not in have:
                _call("POST", f"/memories/{out['library']}/documents?language=en", user=True,
                      files={"file": (name, f"[{d.id}] {d.title}\n\n{d.text}".encode(), "text/markdown")})
    if "workflow" not in out:
        out["workflow"] = _call("POST", "/workflows", json={
            "name": "Alert to work order", "isActive": True,
            "description": "Detector alert in; explanation, checks and draft work order out."})["id"]
        _call("POST", f"/workflows/{out['workflow']}/steps",
              json={"name": "Explain the alert", "stepType": 1, "agentId": out["agent"]})
    IDS.write_text(json.dumps(out, indent=1) + "\n")
    return out


def ready() -> bool:
    load_env()
    return {"agent", "workflow"} <= ids().keys() and bool(os.environ.get("EVOLUS_API_KEY"))


def _flatten(messages: list[dict]) -> str:
    """One text for Evolus: instructions, the conversation so far, then the request. No role headings,
    which the model copies into its answer."""
    system = [m["content"] for m in messages if m["role"] == "system"]
    *earlier, last = [m for m in messages if m["role"] != "system"]
    parts = ["Instructions:\n" + "\n".join(system) + "\nReply once, without role labels."] if system else []
    if earlier:
        parts.append("Context and conversation so far:\n" + "\n\n".join(
            f"{'Technician' if m['role'] == 'user' else 'Copilot'}: {m['content']}" for m in earlier))
    parts.append("Request:\n" + last["content"])
    return "\n\n".join(parts)


def agent_llm(messages: list[dict], max_tokens: int = 700) -> str:
    """One stateless question to the Evolus agent (chat)."""
    r = _call("POST", f"/agents/{ids()['agent']}/ask", timeout=180,
              json={"content": _flatten(messages), "skipChatHistory": True})
    return r["answer"]


def workflow_llm(messages: list[dict], max_tokens: int = 700, wait: float = 180) -> str:
    """Run the 'Alert to work order' workflow and return its output (explain)."""
    wf = ids()["workflow"]
    run = _call("POST", f"/workflows/{wf}/execute", files={"input": (None, _flatten(messages))})
    t0 = time.time()
    while time.time() - t0 < wait:
        ex = _call("GET", f"/workflows/{wf}/executions/{run['executionId']}")
        if ex["status"] == "Completed":  # no Output step: the result is the last step's output
            return ex["output"] or list((ex.get("stepOutputs") or {}).values())[-1]
        if ex["status"] == "Failed":
            raise RuntimeError(f"Evolus workflow failed: {ex.get('error')}")
        time.sleep(2)
    raise TimeoutError("Evolus workflow did not finish in time")


if __name__ == "__main__":
    if sys.argv[1:] == ["setup"]:
        print(json.dumps(setup(), indent=1))
