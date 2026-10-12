import pytest

from copilot import evolus


@pytest.fixture
def fake_api(monkeypatch):
    monkeypatch.setattr(evolus, "ids", lambda: {"agent": "a1", "workflow": "w1"})
    monkeypatch.setattr(evolus.time, "sleep", lambda s: None)
    calls = []

    def install(executions):
        def _call(method, path, **kw):
            calls.append((method, path, kw))
            if path.endswith("/execute"):
                return {"executionId": "e1"}
            if path.endswith("/ask"):
                return {"answer": "from agent"}
            return executions.pop(0)
        monkeypatch.setattr(evolus, "_call", _call)
        return calls
    return install


def test_workflow_polls_until_done_and_falls_back_to_last_step(fake_api):
    calls = fake_api([{"status": "Running"}, {"status": "Completed", "output": "", "stepOutputs": {"1": "{}"}}])
    assert evolus.workflow_llm([{"role": "user", "content": "alert"}]) == "{}"
    assert calls[0][2]["files"]["input"][1] == "Request:\nalert"


def test_flatten_keeps_roles_out_of_headings():
    text = evolus._flatten([{"role": "system", "content": "rules"}, {"role": "user", "content": "ctx"},
                            {"role": "assistant", "content": "earlier answer"}, {"role": "user", "content": "q"}])
    assert "##" not in text and "Copilot: earlier answer" in text and text.endswith("Request:\nq")


def test_failed_workflow_raises(fake_api):
    fake_api([{"status": "Failed", "error": "model down"}])
    with pytest.raises(RuntimeError, match="model down"):
        evolus.workflow_llm([{"role": "user", "content": "alert"}])


def test_agent_ask_is_stateless(fake_api):
    calls = fake_api([])
    assert evolus.agent_llm([{"role": "user", "content": "q"}]) == "from agent"
    assert calls[0][2]["json"]["skipChatHistory"] is True
