"""Load MetroPT-3 and its failure reports (from the dataset's own description PDF)."""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
METROPT = ROOT / "data" / "metropt3" / "MetroPT3(AirCompressor).csv"

ANALOG = ["TP2", "TP3", "H1", "DV_pressure", "Reservoirs", "Oil_temperature", "Motor_current"]
DIGITAL = ["COMP", "DV_eletric", "Towers", "MPG", "LPS", "Pressure_switch", "Oil_level", "Caudal_impulses"]

# Failure reports, "Data Description_Metro.pdf" (UCI 791). All air leaks, high stress.
FAILURES = pd.DataFrame(
    [
        ("2020-04-18 00:00", "2020-04-18 23:59", "Air leak", None),
        ("2020-05-29 23:30", "2020-05-30 06:00", "Air leak", "2020-04-30 12:00"),
        ("2020-06-05 10:00", "2020-06-07 14:30", "Air leak", "2020-06-08 16:00"),
        ("2020-07-15 14:30", "2020-07-15 19:00", "Air leak", "2020-07-16 00:00"),
    ],
    columns=["start", "end", "failure", "maintenance"],
).assign(start=lambda d: pd.to_datetime(d.start), end=lambda d: pd.to_datetime(d.end))

TRAIN_END = pd.Timestamp("2020-04-01")  # fit "normal" only on Feb–Mar, well before failure #1


def load_metropt(path=METROPT) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"], usecols=["timestamp", *ANALOG, *DIGITAL])
    return df.set_index("timestamp").sort_index()
