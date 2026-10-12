"""Check SUBMISSION.md against lablab's limits. Exit 1 if any limit is broken."""
import re
import sys
from pathlib import Path

text = (Path(__file__).parent / "SUBMISSION.md").read_text()
sec = dict(re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M))
title, short, long_ = (sec[k].strip() for k in ("Title", "Short description", "Long description"))
checks = [("title", len(title), "chars", len(title) <= 50),
          ("short description", len(" ".join(short.split())), "chars", len(" ".join(short.split())) <= 255),
          ("long description", len(long_.split()), "words", len(long_.split()) >= 100)]
for name, n, unit, ok in checks:
    print(f"{'OK  ' if ok else 'FAIL'} {name}: {n} {unit}")
sys.exit(0 if all(c[3] for c in checks) else 1)
