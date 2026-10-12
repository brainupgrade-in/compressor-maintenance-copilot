import numpy as np
import pandas as pd

from copilot.detector import Detector


def test_detector_flags_shift_and_names_the_feature():
    idx = pd.date_range("2020-01-01", periods=2000, freq="10min")
    rng = np.random.default_rng(0)
    feats = pd.DataFrame({"a": rng.normal(0, 1, 2000), "b": rng.normal(5, 1, 2000),
                          "c": rng.normal(0, 1, 2000)}, index=idx)
    det = Detector.fit(feats.iloc[:1500])
    shifted = feats.copy()
    shifted.iloc[1800:1900, 1] += 15  # feature "b" drifts for ~17 h
    alerts = det.alerts(shifted)
    during = alerts[(alerts.index >= idx[1800]) & (alerts.index < idx[1900])]
    clean = alerts[(alerts.index >= idx[1500]) & (alerts.index < idx[1800])]
    assert len(during) >= 90                                  # drift is caught almost throughout
    assert during.top_features.str.startswith("b").all()      # and blamed on the right feature
    assert len(clean) <= 3                                    # unseen normal data stays quiet
