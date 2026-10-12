"""Maintenance agent: alert -> plain-language explanation, cited lookup, draft work order, escalation.

The model is an open model on AMD GPUs via AMD Token Factory (AMD_VLLM_* in .env). Safety rules are enforced
in code after the model answers, not only in the prompt.
"""
import json
import os
import re
from pathlib import Path

import pandas as pd
import requests

from .detector import Detector
from .kb import Doc, search

GLOSSARY = {
    "starts": "compressor starts per 10 min",
    "duty_cycle": "share of time the compressor is loading (duty cycle)",
    "Reservoirs_mean": "average main reservoir pressure",
    "TP3_mean": "average pneumatic panel pressure (TP3)",
    "TP2_mean": "average compressor outlet pressure (TP2)",
    "H1_mean": "average pressure after the separator (H1)",
    "DV_pressure_mean": "average dryer discharge pressure drop (DV_pressure)",
    "Oil_temperature_mean": "average oil temperature",
    "Motor_current_mean": "average motor current",
    "Oil_temperature_std": "oil temperature variability",
    "Motor_current_std": "motor current variability",
    "TP2_std": "outlet pressure variability",
    "TP3_std": "panel pressure variability",
    "Reservoirs_std": "reservoir pressure variability",
}
UNSAFE = re.compile(
    r"\b(safe to (run|operate|continue|keep)|no need to (stop|inspect)|can keep running)\b", re.I)
URGENCY = {"low", "medium", "high", "critical"}
DEFERS = re.compile(r"\b(whether|if|not|neither|cannot|can't|never|how long)\b[^.\n]{0,40}$", re.I)


def _unsafe_claims(text: str) -> list[re.Match]:
    """Safe-to-run claims, skipping ones that defer the call ("whether it is safe to run is the lead's call")."""
    return [m for m in UNSAFE.finditer(text) if not DEFERS.search(text[max(0, m.start() - 50):m.start()])]

SYSTEM = """You are a maintenance copilot for an industrial air compressor (APU-300).
You get sensor evidence from an anomaly detector and excerpts from the manual and past work orders.
Rules:
- Use only the evidence and excerpts given. Cite excerpts by their id in square brackets, e.g. [manual#3.1].
- Never say the machine is safe to run or that no inspection is needed. The decision belongs to the maintenance lead.
- If the evidence does not clearly match a known fault, say so and set escalate to true.
- Write in plain English only.
Answer with one JSON object only, with these keys:
explanation (2-3 plain sentences for a technician), likely_cause, confidence (0 to 1),
urgency (low|medium|high|critical), checks (list of short steps), citations (list of excerpt ids),
work_order {title, priority, checks, parts}, escalate (true/false), escalate_reason."""

CHAT_SYSTEM = (
    "You answer a maintenance technician's questions about the current compressor alert. "
    "Use only the alert evidence and excerpts; cite excerpt ids in square brackets. "
    "Never decide whether the machine is safe to run; say that decision belongs to the maintenance lead. "
    "If the excerpts do not answer the question, say so. Write in plain English only.")


def load_env(path=Path(__file__).resolve().parent.parent / ".env"):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def describe_alert(det: Detector, feats: pd.DataFrame, ts) -> dict:
    """Plain facts about one alert window: which features deviate, which way, by how much."""
    z = det.zscores(feats.loc[[ts]]).iloc[0].dropna()
    evidence = []
    for f in z.abs().sort_values(ascending=False).head(4).index:
        evidence.append({
            "feature": f,
            "meaning": GLOSSARY.get(f, f),
            "direction": "higher" if z[f] > 0 else "lower",
            "z": round(float(z[f]), 1),
            "value": round(float(feats.loc[ts, f]), 3),
            "normal": round(float(det.median[f]), 3),
        })
    score = float(det.smoothed_score(feats).loc[ts])
    return {"time": str(ts), "score": round(score, 2), "threshold": round(det.threshold, 2),
            "evidence": evidence}


def _query(alert: dict) -> str:
    words = " ".join(f"{e['meaning']} {e['direction']}" for e in alert["evidence"])
    return f"compressor fault symptoms {words} leak pressure duty cycle starts"


def call_llm(messages: list[dict], max_tokens: int = 700) -> str:
    """One chat completion against the AMD endpoint (OpenAI-compatible)."""
    load_env()
    base = os.environ.get("AMD_VLLM_BASE_URL", "").rstrip("/")
    if not base or "<" in base:
        raise RuntimeError("AMD endpoint not configured: set AMD_VLLM_BASE_URL in .env")
    headers = {"Authorization": f"Bearer {os.environ.get('AMD_VLLM_API_KEY') or 'EMPTY'}"}
    model = os.environ.get("AMD_VLLM_MODEL")
    if not model:
        model = requests.get(f"{base}/models", headers=headers, timeout=15).json()["data"][0]["id"]
    r = requests.post(f"{base}/chat/completions", headers=headers, timeout=120,
                      json={"model": model, "messages": messages, "max_tokens": max_tokens,
                            "temperature": 0.2})
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _parse(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in model reply")
    return json.loads(m.group(0))


def _sources(docs: list[Doc]) -> list[dict]:
    return [{"id": d.id, "title": d.title} for d in docs]


def guard(result: dict, docs: list[Doc]) -> dict:
    """Enforce the grounding and safety rules on a model answer."""
    out = dict(result)
    reasons = []
    cited = [str(c).strip("[] ") for c in out.get("citations") or []]
    out["citations"] = [c for c in cited if c in {d.id for d in docs}]
    if len(out["citations"]) < len(cited):
        reasons.append("model cited documents it was not given")
    if not out["citations"]:
        reasons.append("answer is not grounded in the manual or work orders")
    if UNSAFE.search(json.dumps(out)):
        reasons.append("model made a safe-to-run judgement, which belongs to the maintenance lead")
        for k in ("explanation", "likely_cause"):
            if isinstance(out.get(k), str):
                out[k] = UNSAFE.sub("[removed: run/stop decision belongs to the maintenance lead]", out[k])
    try:
        out["confidence"] = float(out.get("confidence", 0))
    except (TypeError, ValueError):
        out["confidence"] = 0.0
    if out["confidence"] < 0.6:
        reasons.append(f"low confidence ({out['confidence']:.2f})")
    if out.get("urgency") not in URGENCY:
        out["urgency"] = "high"
    if reasons:
        out["escalate"] = True
        out["escalate_reason"] = "; ".join(filter(None, [out.get("escalate_reason") or "", *reasons]))
    out["sources"] = _sources(docs)
    return out


def explain(alert: dict, llm=call_llm) -> dict:
    docs = search(_query(alert), k=4)
    excerpts = "\n\n".join(f"[{d.id}] {d.title}\n{d.text[:1500]}" for d in docs)
    user = f"Detector evidence (JSON):\n{json.dumps(alert, indent=1)}\n\nExcerpts:\n{excerpts}"
    try:
        result = _parse(llm([{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]))
    except Exception as e:  # failed or unreadable answer: never guess, hand to a person
        return {"escalate": True, "escalate_reason": f"agent could not produce an answer ({e})",
                "urgency": "high", "citations": [], "confidence": 0.0, "sources": _sources(docs)}
    return guard(result, docs)


def chat(question: str, alert: dict, history: list[dict] | None = None, llm=call_llm) -> dict:
    docs = search(question + " " + _query(alert), k=4)
    excerpts = "\n\n".join(f"[{d.id}] {d.title}\n{d.text[:1200]}" for d in docs)
    messages = [{"role": "system", "content": CHAT_SYSTEM},
                {"role": "user", "content": f"Alert: {json.dumps(alert)}\n\nExcerpts:\n{excerpts}"},
                *(history or []), {"role": "user", "content": question}]
    try:
        text = llm(messages, max_tokens=800)
    except Exception as e:
        return {"answer": f"The agent is unavailable ({e}). Please ask the maintenance lead.",
                "citations": []}
    if claims := _unsafe_claims(text):
        for m in reversed(claims):
            text = text[:m.start()] + "[removed]" + text[m.end():]
        text += "\n\nWhether to keep running is the maintenance lead's decision."
    cited = sorted({c for c in re.findall(r"\[([\w#.\-]+)\]", text) if c in {d.id for d in docs}})
    return {"answer": text, "citations": cited}
