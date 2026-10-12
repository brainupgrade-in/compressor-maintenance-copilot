"""Compressor Maintenance Copilot — Streamlit app."""
import os

import pandas as pd
import streamlit as st

from copilot import agent, evolus, saved
from copilot.ai4i import run as run_ai4i
from copilot.data import TRAIN_END
from copilot.detector import Detector
from copilot.evaluate import evaluate, load_features
from copilot.kb import load_docs

st.set_page_config(page_title="Compressor Copilot", layout="wide")
st.title("Compressor Maintenance Copilot")
agent.load_env()
EVOLUS = evolus.ready()
WIDGET_URL = "https://agenticai-compressor.brainupgrade.in/widget/"  # k8s/widget.yaml; its domain is whitelisted
st.caption("Early fault warnings, explained by an open model "
           f"({os.environ.get('AMD_VLLM_MODEL') or 'not configured'}) running on AMD GPUs via AMD Token Factory"
           + (", orchestrated by an Evolus agent and workflow." if EVOLUS else "."))


@st.cache_data
def metropt():
    feats = load_features()
    det = Detector.fit(feats[feats.index < TRAIN_END])
    score = det.smoothed_score(feats)
    table, fa_day, fa_pct = evaluate(feats, det)
    return feats, det, score, table, fa_day, fa_pct


@st.cache_data
def ai4i():
    _, table, precision, recall, flagged = run_ai4i()
    return table, precision, recall, flagged


@st.cache_data
def docs_by_id():
    return {d.id: d for d in load_docs()}


def show_result(res: dict):
    if res.get("escalate"):
        st.error(f"Escalated to the maintenance lead: {res.get('escalate_reason', '')}")
    c1, c2 = st.columns(2)
    c1.metric("Urgency", str(res.get("urgency", "-")).upper())
    c2.metric("Agent confidence", f"{res.get('confidence', 0):.0%}")
    if res.get("explanation"):
        st.markdown(f"**What is happening.** {res['explanation']}")
    if res.get("likely_cause"):
        st.markdown(f"**Likely cause.** {res['likely_cause']}")
    if res.get("checks"):
        st.markdown("**Checks to do**")
        st.markdown("\n".join(f"1. {c}" for c in res["checks"]))
    wo = res.get("work_order")
    if isinstance(wo, dict) and wo.get("title"):
        with st.expander(f"Draft work order: {wo['title']}", expanded=True):
            st.write(f"Priority: {wo.get('priority', '-')}")
            for c in wo.get("checks") or []:
                st.write(f"- {c}")
            if wo.get("parts"):
                st.write("Parts to have ready: " + ", ".join(map(str, wo["parts"])))
    if res.get("citations"):
        st.markdown("**Sources cited**")
        for cid in res["citations"]:
            d = docs_by_id().get(cid)
            if d:
                with st.expander(f"{cid}: {d.title}"):
                    st.markdown(d.text)


tab1, tab2, tab3 = st.tabs(["Air compressor (MetroPT-3)", "Milling machine (AI4I 2020)", "Ask the Evolus agent"])

with tab1:
    feats, det, score, table, fa_day, fa_pct = metropt()
    st.caption("Real compressor data (UCI MetroPT-3, CC BY 4.0). Detector learnt 'normal' from Feb–Mar 2020 only.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Recorded failures warned before onset", f"{int(table.warned_before_onset.sum())} / 4")
    c2.metric("False-alert episodes per day", f"{fa_day:.2f}")
    c3.metric("Time in false alert", f"{fa_pct:.1f}%")

    day = st.date_input("Day to inspect", value=pd.Timestamp("2020-05-26"),
                        min_value=feats.index.min().date(), max_value=feats.index.max().date())
    lo, hi = pd.Timestamp(day) - pd.Timedelta("2D"), pd.Timestamp(day) + pd.Timedelta("2D")
    st.line_chart(pd.DataFrame({"anomaly score": score[lo:hi], "alert threshold": det.threshold}))

    alerts = det.alerts(feats[lo:hi])
    if alerts.empty:
        st.info("No alerts in this window. Try 26 May, 3 Jun or 17 Apr 2020.")
    else:
        # one row per alert episode (a new episode starts after a 1 h gap)
        starts = alerts.index.to_series().diff().gt(pd.Timedelta("1h")).cumsum()
        episodes = alerts.groupby(starts).head(1)
        ts = st.selectbox("Alert", episodes.index,
                          format_func=lambda t: f"{t:%d %b %Y %H:%M} · score {alerts.loc[t, 'score']:.1f} · "
                                                f"{alerts.loc[t, 'top_features']}")
        alert = agent.describe_alert(det, feats, ts)
        with st.expander("Detector evidence sent to the agent"):
            st.dataframe(pd.DataFrame(alert["evidence"]), width="stretch", hide_index=True)

        key = f"res-{ts}"
        rec = saved.load().get(str(ts))
        b1, b2 = st.columns([2, 3])
        if b1.button("Explain with the AMD-hosted agent", type="primary"):
            if rec:  # recorded from a live run: instant, and spares the shared AMD key
                st.session_state[key] = rec["result"]
                st.session_state[f"src-{ts}"] = f"Saved answer from a live run on {rec['recorded']} ({rec['via']})."
            else:
                with st.spinner("Asking the agent…"):
                    st.session_state[key] = agent.explain(alert, llm=evolus.workflow_llm if EVOLUS else agent.call_llm)
                st.session_state[f"src-{ts}"] = "Live answer."
            st.session_state[f"chat-{ts}"] = []
        if rec and b2.button("Run it live on AMD now (about 30–60 s)"):
            with st.spinner("Asking the agent live…"):
                st.session_state[key] = agent.explain(alert, llm=evolus.workflow_llm if EVOLUS else agent.call_llm)
            st.session_state[f"src-{ts}"] = "Live answer."
            st.session_state[f"chat-{ts}"] = []
        if key in st.session_state:
            st.caption(st.session_state.get(f"src-{ts}", ""))
            show_result(st.session_state[key])

            st.subheader("Ask the copilot")
            hist = st.session_state.setdefault(f"chat-{ts}", [])
            for m in hist:
                st.chat_message(m["role"]).write(m["content"])
            if q := st.chat_input("e.g. What did we do last time this happened?"):
                st.chat_message("user").write(q)
                ans = agent.chat(q, alert, history=hist, llm=evolus.agent_llm if EVOLUS else agent.call_llm)
                st.chat_message("assistant").write(ans["answer"])
                hist += [{"role": "user", "content": q}, {"role": "assistant", "content": ans["answer"]}]

    with st.expander("Recorded failures and lead times"):
        st.dataframe(table, width="stretch", hide_index=True)
        st.caption("Failure reports from the dataset description. Lead time capped at the 48 h lookback.")

with tab2:
    t, p, r, n = ai4i()
    st.caption("Synthetic milling-machine data (UCI AI4I 2020, CC BY 4.0). This plant has labelled failure "
               "history, so the copilot uses a supervised classifier per failure mode.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Failures caught (held-out runs)", f"{r:.0%}")
    c2.metric("Flags that were real failures", f"{p:.0%}")
    c3.metric("Runs flagged", f"{n} of 5,000")
    st.dataframe(t, width="stretch", hide_index=True)
    st.caption("Tool-wear and random failures are not predictable from these sensors by design of the dataset.")

with tab3:
    st.caption("The Evolus website widget: the same agent and knowledge library, as a plant would embed it on its "
               "intranet. Ask about faults, parts or past repairs.")
    st.components.v1.iframe(WIDGET_URL, height=640)

st.caption("Manual and work orders in kb/ are synthetic, written for this demo.")
