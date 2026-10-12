"""Saved answers from live runs, so the public demo answers instantly and spares the shared AMD key.

`python -m copilot.saved record` runs the live path (Evolus workflow on the AMD model, same guardrails)
for the alerts the demo walks through and stores the results in saved_answers.json.
"""
import json
from datetime import date

import pandas as pd

from . import agent, evolus
from .data import ROOT, TRAIN_END
from .detector import Detector
from .evaluate import load_features

FILE = ROOT / "saved_answers.json"
DEMO_ALERTS = ["2020-04-17 10:00:00", "2020-05-26 09:50:00", "2020-06-01 15:20:00", "2020-06-03 10:40:00"]


def load() -> dict:
    return json.loads(FILE.read_text()) if FILE.exists() else {}


def record():
    feats = load_features()
    det = Detector.fit(feats[feats.index < TRAIN_END])
    llm = evolus.workflow_llm if evolus.ready() else agent.call_llm
    out = load()
    for t in DEMO_ALERTS:
        res = agent.explain(agent.describe_alert(det, feats, pd.Timestamp(t)), llm=llm)
        out[t] = {"result": res, "recorded": date.today().isoformat(),
                  "via": "Evolus workflow" if llm is not agent.call_llm else "AMD Token Factory"}
        print(t, res.get("urgency"), res.get("confidence"), res.get("citations"))
    FILE.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    record()
