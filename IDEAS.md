# Idea shortlist (3 Oct 2026) — decision pending (Rajesh)

> **Update after reading the four track briefs:** every project must select one main track, and the
> GST idea fits none of them. Commerce is about customers (shopping, support, churn, demand) and
> Industry is about factories. New recommendation: **idea 0** below. Ideas 1–2 stay as fallbacks
> only if the Evolus prize alone is the goal.

## 0. Hospital discharge companion (recommended; Health and Wellbeing + Evolus prize)
- **User:** a patient going home from an Indian hospital and the ward nurse who discharges them.
- **Process:** discharge summary PDF → extract diagnosis, medicines, doses, follow-ups, red-flag
  symptoms → plain-language explanation in the patient's own language (Hindi, Marathi …) →
  day-by-day medicine and follow-up schedule → patient asks questions by chat → anything that
  matches a red flag goes to the nurse, not answered by the bot.
- **Evolus blocks:** document extractor (discharge summary → JSON), AI Tools `simplify`, `translate`
  and `anonymize`, workflow (PDF in → schedule out), knowledge library (hospital discharge
  instructions), chat widget for the patient.
- **Why AMD matters to the story:** patient data goes to our own open model on AMD, not to a
  third-party LLM API. Privacy is the business reason for self-hosting, not just a rule we met.
- **Measurable gain:** fewer "what do I take when" calls to the ward; red flags reach a nurse sooner.
- **Fits the brief:** clear patient/staff need, responsible handling (redaction, escalation instead
  of medical advice), understandable output, measurable workload reduction.
- **Risk:** must never give medical advice beyond the summary. Synthetic discharge summaries only.

Scored against the four judging criteria. Every idea runs its main agent on our own vLLM on an
AMD MI300X, and uses at least two Evolus building blocks so it also qualifies for the Evolus prize.

## 1. GST input-tax-credit reconciliation agent (no main-track fit)
- **User:** the accountant at an Indian SME (us: UTS / GUG). Monthly chore, done by hand today.
- **Process:** purchase invoices (PDF/email) → extract GSTIN, invoice no., taxable value, tax →
  match against the GSTR-2A/2B download → flag missing, mismatched or unfiled supplier invoices →
  draft the supplier chase email → hand doubtful cases to a person.
- **Evolus blocks:** document extractor (invoice → JSON), workflow (email in → match → result),
  AI Tool `email` (supplier chase), knowledge library (GST ITC rules).
- **Why it scores:** real process with money at stake (unclaimed ITC); measurable (₹ recovered,
  hours saved); we have real data shapes from `GUG/invoices` (GSTR2A-ITC-STATUS.md); India-specific, so
  original next to the generic "invoice intake" sample on the track page.
- **Risk:** demo data must be synthetic (no real GSTINs or supplier data in a public repo).

## 2. Receivables agent that understands TDS
- **User:** a small services firm billing corporates / brokers who pay net of 10% TDS.
- **Process:** bank statement + invoices → match payments → classify the short payment as TDS
  credit vs real dispute → reconcile with Form 26AS → chase only the true receivables.
- **Evolus blocks:** extractor (bank statement, invoices), workflow, AI Tool `email`.
- **Why:** same pain we see in AR-STATUS.md; narrower but sharp. Overlaps idea 1; could be its phase 2.

## 3. Fleet exception desk for GPS tracking (Intelligent Industry track)
- **User:** fleet operations desk of a logistics SME.
- **Process:** GPS alerts + driver messages → triage (breakdown, route deviation, idle, tamper) →
  open a ticket, call the right workflow, summarise the day for the manager.
- **Evolus blocks:** workflow, knowledge library (SOPs), AI Tool `summarize`, chat widget.
- **Why:** our own domain (gug-device-server); vivid demo. **Risk:** needs a believable live alert
  feed; less "documents in, data out", so weaker Evolus fit.

## Not chosen
Generic support-desk RAG and meeting-minutes bots: the track page lists them as samples, so they
score low on originality.
