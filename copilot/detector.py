"""Unsupervised detector: 10-minute window features, robust z-scores against a Feb–Mar baseline.

No language model here: alerts must be fast, cheap and explainable. Each alert carries the
features that drove it, which the agent later turns into plain language.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import ANALOG

WINDOW = "10min"
SMOOTH = 6  # windows -> 1 hour


def window_features(df: pd.DataFrame) -> pd.DataFrame:
    g = df.resample(WINDOW)
    feats = pd.concat(
        {
            **{f"{c}_mean": g[c].mean() for c in ANALOG},
            **{f"{c}_std": g[c].std() for c in ["TP2", "TP3", "Reservoirs", "Motor_current", "Oil_temperature"]},
            # compressor duty cycle and how often it switches on: leaks make it work harder
            "duty_cycle": g["COMP"].mean().rsub(1.0),  # COMP=0 while loading (motor running)
            "starts": df["COMP"].diff().eq(-1).resample(WINDOW).sum(),
            "samples": g["TP2"].count(),
        },
        axis=1,
    )
    return feats[feats["samples"] >= 30].drop(columns="samples")  # skip windows with missing data


@dataclass
class Detector:
    median: pd.Series
    mad: pd.Series
    threshold: float
    smooth: int = SMOOTH  # windows to smooth over; 1 = no smoothing (row-level data such as AI4I)

    @classmethod
    def fit(cls, feats: pd.DataFrame, quantile: float = 0.999, smooth: int = SMOOTH) -> "Detector":
        med = feats.median()
        mad = 1.4826 * (feats - med).abs().median()
        # bimodal signals (TP2, DV_pressure flip between ~0 and ~9 bar) give a near-zero MAD;
        # floor the scale at the ordinary std so they don't saturate
        scale = np.maximum(mad, feats.std()).replace(0, 1.0)
        det = cls(med, scale, threshold=np.inf, smooth=smooth)
        det.threshold = float(det.smoothed_score(feats).quantile(quantile))
        return det

    def zscores(self, feats: pd.DataFrame) -> pd.DataFrame:
        return ((feats - self.median) / self.mad).clip(-50, 50)

    def score(self, feats: pd.DataFrame) -> pd.Series:
        z = self.zscores(feats).abs().to_numpy()
        z = np.where(np.isnan(z), -np.inf, z)
        top3 = np.sort(z, axis=1)[:, -3:]  # top-3 deviating features
        top3 = np.where(np.isinf(top3), np.nan, top3)
        return pd.Series(np.nanmean(top3, axis=1), index=feats.index)

    def smoothed_score(self, feats: pd.DataFrame) -> pd.Series:
        return self.score(feats).rolling(self.smooth, min_periods=self.smooth).median()

    def alerts(self, feats: pd.DataFrame) -> pd.DataFrame:
        s = self.smoothed_score(feats)
        z = self.zscores(feats)
        hot = s[s > self.threshold]
        za = z.loc[hot.index].abs().fillna(-1).to_numpy()
        cols = np.array(z.columns)
        top = pd.Series([", ".join(cols[np.argsort(-row)[:3]]) for row in za], index=hot.index, dtype=object)
        return pd.DataFrame({"score": hot, "top_features": top})
