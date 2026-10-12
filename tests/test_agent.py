import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from copilot import agent

ALERT = {"time": "2020-05-27 10:00:00", "score": 7.1, "threshold": 5.44, "evidence": [
    {"feature": "starts", "meaning": "compressor starts per 10 min", "direction": "higher", "z": 18.1,
     "value": 6.0, "normal": 2.0},
    {"feature": "Reservoirs_mean", "meaning": "average main reservoir pressure", "direction": "lower",
     "z": -1.8, "value": 8.7, "normal": 9.0}]}

GOOD = {"explanation": "The compressor starts far more often and reservoir pressure is lower, "
                       "which matches an air leak [manual#3.1].",
        "likely_cause": "air leak downstream of the reservoirs", "confidence": 0.8, "urgency": "high",
        "checks": ["pressure decay test with consumers isolated"], "citations": ["manual#3.1"],
        "work_order": {"title": "Suspected air leak", "priority": "High", "checks": [], "parts": []},
        "escalate": False, "escalate_reason": ""}


def fake(reply):
    return lambda messages, max_tokens=700: reply if isinstance(reply, str) else json.dumps(reply)


def test_good_answer_passes_and_lists_sources():
    out = agent.explain(ALERT, llm=fake(GOOD))
    assert out["escalate"] is False
    assert out["citations"] == ["manual#3.1"]
    assert any(s["id"] == "manual#3.1" for s in out["sources"])


def test_invented_citation_is_dropped_and_escalated():
    out = agent.explain(ALERT, llm=fake({**GOOD, "citations": ["WO-9999-999"]}))
    assert out["citations"] == [] and out["escalate"] is True
    assert "not given" in out["escalate_reason"]


def test_safe_to_run_judgement_is_removed_and_escalated():
    out = agent.explain(ALERT, llm=fake({**GOOD, "explanation": "Minor leak, safe to run until Friday."}))
    assert out["escalate"] is True
    assert "safe to run" not in out["explanation"].lower()


def test_low_confidence_escalates():
    assert agent.explain(ALERT, llm=fake({**GOOD, "confidence": 0.3}))["escalate"] is True


def test_unreadable_reply_escalates_without_crashing():
    out = agent.explain(ALERT, llm=fake("I think it is probably fine"))
    assert out["escalate"] is True and "could not produce" in out["escalate_reason"]


def test_chat_strips_run_decision_and_keeps_valid_citations():
    reply = "Last time it was the drain valve [WO-2019-114]. It is safe to keep running [WO-0000-000]."
    out = agent.chat("what did we do last time?", ALERT, llm=fake(reply))
    assert "WO-2019-114" in out["citations"] and "WO-0000-000" not in out["citations"]
    assert "safe to keep" not in out["answer"].lower() and "maintenance lead" in out["answer"]


@pytest.fixture
def mock_vllm(monkeypatch):
    seen = {}

    class H(BaseHTTPRequestHandler):
        def _send(self, d):
            b = json.dumps(d).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            self._send({"data": [{"id": "test-model"}]})

        def do_POST(self):
            seen["auth"] = self.headers["Authorization"]
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            self._send({"choices": [{"message": {"content": json.dumps(GOOD)}}]})

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("AMD_VLLM_BASE_URL", f"http://127.0.0.1:{srv.server_port}/v1")
    monkeypatch.setenv("AMD_VLLM_API_KEY", "testkey")
    monkeypatch.delenv("AMD_VLLM_MODEL", raising=False)
    monkeypatch.setattr(agent, "load_env", lambda *a, **k: None)  # never read the real .env in tests
    yield seen
    srv.shutdown()


def test_real_http_client_against_mock_endpoint(mock_vllm):
    out = agent.explain(ALERT)  # default llm = call_llm over HTTP
    assert out["escalate"] is False and out["citations"] == ["manual#3.1"]
    assert mock_vllm["auth"] == "Bearer testkey"
    assert mock_vllm["body"]["model"] == "test-model"


def test_chat_keeps_deferring_sentences_and_removes_claims():
    keep = agent.chat("run till Friday?", ALERT, llm=fake(
        "Whether the machine is safe to run is a decision for the maintenance lead [manual#3.1]."))
    assert "[removed]" not in keep["answer"] and "safe to run" in keep["answer"]
    cut = agent.chat("run till Friday?", ALERT, llm=fake("It is safe to run until Friday [manual#3.1]."))
    assert "safe to run" not in cut["answer"] and "maintenance lead's decision" in cut["answer"]
