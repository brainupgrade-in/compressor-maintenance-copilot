# Spec: Compressor Maintenance Copilot

Track: **Intelligent Industry** · Partner prize: **Evolus** · UI: **Streamlit** · Approved 4 Oct 2026.

## Problem and user
- **User:** maintenance lead at a small/mid Indian factory; one person covering many machines, no data scientist.
- **Problem:** sensor data exists but nobody watches it. Faults such as air leaks are found when the
  machine stops. Manuals and past repair notes are not searched under pressure.
- **Outcome we promise:** earlier warning of compressor faults, with a plain-language explanation and a
  ready work order, so the lead acts before downtime.

## Scope (must-have)
1. **Detector** (no LLM): unsupervised anomaly model on MetroPT-3 sensor windows, trained only on
   data before the first failure. Emits alerts with the sensors that drove them.
2. **Agent** on our own vLLM endpoint on an AMD MI300X: explains the alert, searches the manual and past
   work orders, drafts a work order, escalates when unsure.
3. **Evolus:** knowledge library (manual + work orders), workflow (alert → explanation → work order),
   chat widget or agent chat for the technician. Driven through the Evolus REST API from our app.
4. **Streamlit app:** replay timeline, alert panel, explanation, draft work order, chat.
5. **Second machine:** AI4I 2020 milling data, same explanation path, to show it generalises.

## Out of scope
Real plant integration, live PLC/SCADA feeds, user accounts, mobile app, model fine-tuning.

## Success criteria (measured, not claimed)
| Metric | Target | How |
|---|---|---|
| Failures warned before onset (MetroPT-3, 4 events) | ≥ 3 of 4 | `python3 -m copilot.evaluate` |
| Median lead time before onset | ≥ 2 h | same |
| False alerts outside failure windows | ≤ 1 per day | same |
| Agent answers grounded in retrieved docs | every work order cites a doc | manual check of 10 alerts |
| Endpoint on AMD | `scripts/vllm_smoke.py` prints PASS | smoke test |

Lead time = onset of the recorded failure window minus the first alert in the preceding 48 h.

## Data
- MetroPT-3 (UCI 791, CC BY 4.0) and AI4I 2020 (UCI 601, CC BY 4.0), fetched by `scripts/download_data.py`
  into `data/` (gitignored). Never committed.
- Manual and work orders under `kb/` are **synthetic**, written for this project, and labelled so.

## Constraints
- Main agent model: open model served by our vLLM on AMD (Gemma 4 if it counts for the Google prize, else Qwen).
- Containerised app, README that runs, MIT licence, no secrets in git.
- Safety: the agent never says a machine is safe to run; it states evidence and escalates.

## Demo (≤ 5 min)
Replay May 2020 → detector fires before the 29–30 May air leak → agent explains, cites past work
order, drafts a new one → technician asks a follow-up → a low-confidence case is escalated →
headline numbers from the evaluation → AI4I second machine in 20 s.
