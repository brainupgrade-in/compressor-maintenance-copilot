"""Second machine: AI4I 2020 milling process (UCI 601, CC BY 4.0).

Unlike MetroPT-3 this dataset has labelled failure history, so the copilot uses a supervised
classifier per failure mode here (anomaly scoring caught only 17 % of failures: AI4I failures are
combinations, e.g. high wear AND high torque, where each value alone looks normal).

    uv run python -m copilot.ai4i
"""
import numpy as np
import pandas as pd

from .data import ROOT

AI4I = ROOT / "data" / "ai4i2020" / "ai4i2020.csv"
MODES = ["TWF", "HDF", "PWF", "OSF", "RNF"]
MODE_NAMES = {"TWF": "tool wear", "HDF": "heat dissipation", "PWF": "power", "OSF": "overstrain", "RNF": "random"}


def load_ai4i(path=AI4I) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def features(d: pd.DataFrame) -> pd.DataFrame:
    rpm, torque = d["Rotational speed [rpm]"], d["Torque [Nm]"]
    return pd.DataFrame({
        "power_W": torque * rpm * 2 * np.pi / 60,
        "temp_gap_K": d["Process temperature [K]"] - d["Air temperature [K]"],
        "rpm": rpm,
        "torque_Nm": torque,
        "tool_wear_min": d["Tool wear [min]"],
        "strain": d["Tool wear [min]"] * torque,
    }, index=d.index)


def run(seed: int = 0):
    """Supervised: AI4I has labelled failure history. One gradient-boosted classifier per failure
    mode; rows are independent synthetic runs, so a stratified random 50/50 split is fair."""
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import train_test_split

    d = load_ai4i()
    f = features(d).assign(type=d["Type"].map({"L": 0, "M": 1, "H": 2}))
    strat = d[MODES].idxmax(axis=1).where(d["Machine failure"] == 1, "none")
    tr, te = train_test_split(d.index, test_size=0.5, random_state=seed, stratify=strat)
    probs = pd.DataFrame(index=te)
    models = {}
    for m in MODES:
        if d.loc[tr, m].sum() < 5:
            continue
        clf = HistGradientBoostingClassifier(random_state=seed).fit(f.loc[tr], d.loc[tr, m])
        models[m] = clf
        probs[m] = clf.predict_proba(f.loc[te])[:, 1]
    flagged = (probs > 0.5).any(axis=1)
    truth = d.loc[te]
    fail = truth["Machine failure"] == 1
    rows = [{"mode": f"{m} ({MODE_NAMES[m]})", "failures": int(truth[m].sum()),
             "flagged": int((flagged & (truth[m] == 1)).sum())} for m in MODES]
    table = pd.DataFrame(rows).assign(recall=lambda t: (t.flagged / t.failures).round(2))
    precision = (flagged & fail).sum() / max(flagged.sum(), 1)
    recall = (flagged & fail).sum() / fail.sum()
    return models, table, float(precision), float(recall), int(flagged.sum())


def main():
    _, table, p, r, n = run()
    print(table.to_string(index=False))
    print(f"\noverall: recall {r:.2f} | precision {p:.2f} | flagged {n} of 5000 held-out runs")


if __name__ == "__main__":
    main()
