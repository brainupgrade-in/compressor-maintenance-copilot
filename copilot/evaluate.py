"""Score the detector against the four recorded MetroPT-3 failures.

    uv run python -m copilot.evaluate
"""
import pandas as pd

from .data import FAILURES, TRAIN_END, load_metropt
from .detector import Detector, window_features

LOOKBACK = pd.Timedelta("48h")


def evaluate(feats: pd.DataFrame, det: Detector) -> tuple[pd.DataFrame, float]:
    alerts = det.alerts(feats[feats.index >= TRAIN_END])
    rows = []
    for i, f in FAILURES.iterrows():
        near = alerts[(alerts.index >= f.start - LOOKBACK) & (alerts.index <= f.end)]
        first = near.index.min() if len(near) else pd.NaT
        lead = (f.start - first).total_seconds() / 3600 if len(near) else None
        rows.append({"failure": f"#{i + 1} {f.start:%d %b %H:%M}", "first_alert": first,
                     "lead_h": None if lead is None else round(lead, 1),
                     "warned_before_onset": lead is not None and lead > 0})
    in_any = pd.Series(False, index=alerts.index)
    for _, f in FAILURES.iterrows():
        in_any |= (alerts.index >= f.start - LOOKBACK) & (alerts.index <= f.end + pd.Timedelta("24h"))
    false = alerts[~in_any]
    # count alert episodes (gaps > 1 h start a new one), per day of evaluated data
    episodes = (false.index.to_series().diff() > pd.Timedelta("1h")).sum() + (1 if len(false) else 0)
    days = (feats.index.max() - TRAIN_END).total_seconds() / 86400
    evaluated = (feats.index >= TRAIN_END).sum()
    false_time_pct = 100 * len(false) / evaluated  # share of evaluated windows in false alert
    return pd.DataFrame(rows), episodes / days, false_time_pct


def load_features():
    from .data import ROOT
    cache = ROOT / "data" / "feats.pkl"
    if cache.exists():
        return pd.read_pickle(cache)
    feats = window_features(load_metropt())
    feats.to_pickle(cache)
    return feats


def main():
    feats = load_features()
    det = Detector.fit(feats[feats.index < TRAIN_END])
    table, fa_per_day, fa_pct = evaluate(feats, det)
    print(table.to_string(index=False))
    warned = int(table.warned_before_onset.sum())
    leads = table.lead_h.dropna()
    print(f"\nwarned before onset: {warned}/4 | median lead: {leads[leads > 0].median() if warned else 0:.1f} h"
          f" | false-alert episodes/day: {fa_per_day:.2f} | time in false alert: {fa_pct:.1f}%"
          f" | threshold: {det.threshold:.2f}")
    print("note: lead time is capped at the 48 h lookback; an alert already on earlier shows as 48 h.")


if __name__ == "__main__":
    main()
