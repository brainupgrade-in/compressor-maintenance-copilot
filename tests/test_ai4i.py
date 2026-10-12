import pytest

from copilot.ai4i import AI4I, run


@pytest.mark.skipif(not AI4I.exists(), reason="run scripts/download_data.py first")
def test_ai4i_classifier_quality_holds():
    _, table, precision, recall, _ = run(seed=0)
    assert recall >= 0.7 and precision >= 0.8
    heat = table[table["mode"].str.startswith("HDF")].iloc[0]
    assert heat.recall >= 0.9
