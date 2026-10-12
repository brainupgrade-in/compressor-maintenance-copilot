"""Fetch the public datasets into data/ (never committed). Stdlib only.

MetroPT-3: UCI 791, CC BY 4.0, doi:10.24432/C5VW3R
AI4I 2020: UCI 601, CC BY 4.0, doi:10.24432/C5HS5C
"""
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
SOURCES = {
    "metropt3": "https://archive.ics.uci.edu/static/public/791/metropt+3+dataset.zip",
    "ai4i2020": "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip",
}


def fetch(name, url):
    out = DATA / name
    if out.exists() and any(out.iterdir()):
        print(f"{name}: already present")
        return
    out.mkdir(parents=True, exist_ok=True)
    print(f"{name}: downloading {url}")
    blob = urllib.request.urlopen(url, timeout=300).read()
    zipfile.ZipFile(io.BytesIO(blob)).extractall(out)
    for f in sorted(out.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(DATA)}  {f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    for n in sys.argv[1:] or SOURCES:
        fetch(n, SOURCES[n])
