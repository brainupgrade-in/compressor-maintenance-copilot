# Compressor Maintenance Copilot

AMD Developer Hackathon: ACT III (lablab.ai) · Track: **Intelligent Industry** · Team **gheware**

Catches compressor faults early, explains them in plain language, and drafts the work order, so a
factory maintenance lead acts before the machine stops. The detector is a classic statistical model.
The agent thinks with an open model (DeepSeek-V4-Flash) running on AMD GPUs through AMD Token
Factory, and runs as an Evolus agent with an Evolus knowledge library and workflow. See [SPEC.md](SPEC.md).

```
sensors ─► detector (statistical, local) ─► alert + evidence
                                              │
                    Evolus workflow "Alert to work order"
                                              │
                    Evolus agent ── Evolus library "Compressor KB" (manual + work orders)
                                              │
                    DeepSeek-V4-Flash on AMD GPUs (AMD Token Factory, OpenAI-compatible)
                                              │
              guardrails in code ─► explanation, checks, cited sources, draft work order
```

## Results so far (detector only, MetroPT-3)
Trained on Feb–Mar 2020 only, threshold fixed from that period, evaluated on Apr–Aug against the four
air leaks in the operator's failure reports.

| Failure (onset) | First alert | Lead time |
|---|---|---|
| 18 Apr 00:00 | 17 Apr 10:00 | 14 h |
| 29 May 23:30 | alert on before 27 May 23:30 | ≥ 48 h (on since 26 May) |
| 5 Jun 10:00 | 3 Jun 10:40 | ≥ 47 h |
| 15 Jul 14:30 | none | missed |

False alerts: 0.13 episodes per day, 4.5 % of evaluated time. Lead time is capped at a 48 h lookback.

## Second machine (AI4I 2020, milling)
This plant has labelled failure history, so the copilot uses a supervised classifier per failure mode
(stratified 50/50 split, three seeds): recall 0.75–0.79, precision 0.86–0.90. Heat-dissipation 100 %,
overstrain ~92 %, power ~70 %; tool-wear and random failures are not predictable by design of the data.

## Agent
`copilot/agent.py` turns an alert into a plain explanation, likely cause, checks, cited sources and a
draft work order, using our open model on AMD. Rules enforced in code, not only in the prompt: citations
must be documents the agent was given; any safe-to-run verdict is removed and escalated; low confidence
or an unreadable answer escalates to a person.

## Evolus
`copilot/evolus.py` builds and drives three Evolus building blocks over the REST API:
- **Knowledge library** "Compressor KB": the manual sections and work orders, one file each, with
  their citation ids.
- **Agent** "Compressor Maintenance Copilot": its model is our own AMD Token Factory connection
  (`own/DeepSeek-V4-Flash`), so Evolus spends no credits on thinking and the model runs on AMD GPUs.
- **Workflow** "Alert to work order": the app's *Explain* button runs it; the technician chat asks
  the agent directly.
- **Website widget**: the same agent as a plant would embed it on its intranet (the app's third tab,
  served from `/widget/`, limited to the demo's domain).

Every Evolus answer still goes through the guardrails above. Without Evolus settings the app calls the
AMD endpoint directly.

## Live demo
https://agenticai-compressor.brainupgrade.in — the four demo alerts show answers recorded from live runs
(`python -m copilot.saved` refreshes them), so the page answers instantly and spares the shared AMD key;
"Run it live on AMD now" and the chat always call the model. Deployed on a k3s cluster with
`k8s/app.yaml`, `k8s/widget.yaml` and `python3 scripts/deploy_spark.py`.

## Run
```bash
uv sync
uv run python scripts/download_data.py      # public UCI datasets into data/ (not committed)
uv run python -m copilot.evaluate           # reproduce the table above
uv run python -m copilot.ai4i               # second machine
uv run python -m copilot.evolus setup      # once: Evolus agent, library, workflow -> evolus.json
uv run streamlit run app.py                 # app on :8501
uv run --group dev pytest -q
```
Docker: `docker build -t compressor-copilot . && docker run --env-file .env -p 8501:8501 compressor-copilot`
(the container downloads the datasets on first start).

Settings go in `.env` (copy `.env.example`): the AMD Token Factory key and base URL (`AMD_VLLM_*`) and,
for Evolus, the application key and space id (plus a personal user key, only to create the library).
AMD endpoint check: `python3 scripts/vllm_smoke.py`

## Data and credits
- MetroPT-3: Davari, Veloso, Ribeiro, Gama (2021), UCI ML Repository, doi:10.24432/C5VW3R, CC BY 4.0.
- AI4I 2020: Matzka (2020), UCI ML Repository, doi:10.24432/C5HS5C, CC BY 4.0.
- `kb/` (manual and work orders) is **synthetic**, written for this demo.

## Licence
MIT, see [LICENSE](LICENSE).
