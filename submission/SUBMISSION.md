# lablab submission — AMD Developer Hackathon: ACT III

Draft text for the lablab form. Limits: title ≤ 50 chars, short description ≤ 255 chars,
long description ≥ 100 words. Check with `python3 submission/check_text.py`.

## Title
Compressor Maintenance Copilot

## Short description
Catches compressor faults hours to days before they stop the line, explains them in plain language with
cited manual pages and past repairs, and drafts the work order. An Evolus agent on an open model running
on AMD GPUs.

## Track and tags
- Track: Intelligent Industry (plus the Evolus partner challenge)
- Tags: AMD, AMD Token Factory, Evolus, DeepSeek, predictive maintenance, anomaly detection, RAG, Streamlit

## Problem statement
In small and mid-sized factories one maintenance lead looks after many machines. The sensors already log
pressure, temperature and motor current, but nobody watches them, so faults such as air leaks are found
when the compressor stops. The manual and past repair notes exist, but nobody searches them under
pressure.

## Intended user
The maintenance lead at a small or mid-sized factory: no data scientist on staff, one person covering
many machines, and the one who decides whether a machine keeps running.

## Long description
Compressor Maintenance Copilot watches compressor sensor data, warns before a fault stops the machine,
and turns each warning into something a maintenance lead can act on.

A statistical detector learns what normal looks like from two months of real data (UCI MetroPT-3, a
metro train's air compressor) and is never tuned on failures. On the four air leaks recorded later that
year it warned before three of them, 14 hours to more than 2 days ahead, with about one false-alert
episode per week.

Each alert goes to an Evolus workflow. Its Evolus agent thinks with DeepSeek-V4-Flash running on AMD
GPUs through AMD Token Factory, connected as our own model, and searches an Evolus knowledge library of
the compressor manual and past work orders. It explains what is happening in plain language, names the
likely cause, lists the checks to run, cites its sources, and drafts the work order with parts to have
ready. The technician can then ask follow-up questions in chat, such as what was done last time.

Safety rules are enforced in code, not only in the prompt: every citation must be a real document, any
"safe to keep running" verdict is removed because that decision belongs to the maintenance lead, and low
confidence or an unreadable answer escalates to a person. A second machine (AI4I 2020 milling data, with
per-failure-mode classifiers) shows that the same flow generalises.

Built with Python, scikit-learn, Streamlit, the Evolus REST API (agent, knowledge library, workflow) and
AMD Token Factory. Open source under MIT; the manual and work orders are synthetic and labelled so.

## Links (to fill)
- Public GitHub repo: (needs the user's yes to publish)
- Demo app URL: https://agenticai-compressor.brainupgrade.in
- Demo video (MP4 ≤ 5 min, < 300 MB): to record
- Slides (PDF): to build
- Cover image (16:9 PNG/JPG): to make
