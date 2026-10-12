"""Local knowledge-base search over kb/ (manual sections + work orders).

Stand-in for the Evolus knowledge library until kickoff; same documents, same citation ids.
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import ROOT

KB = ROOT / "kb"


@dataclass(frozen=True)
class Doc:
    id: str      # citation id, e.g. "manual#3.1" or "WO-2020-150"
    title: str
    text: str


def load_docs() -> list[Doc]:
    docs = []
    manual = (KB / "manual.md").read_text()
    for block in re.split(r"\n(?=###? \d)", manual):
        m = re.match(r"###? (\d+(?:\.\d+)?)\.? (.+)", block)
        if m:
            docs.append(Doc(f"manual#{m.group(1)}", m.group(2).strip(), block.strip()))
    for p in sorted((KB / "work_orders").glob("*.md")):
        text = p.read_text()
        docs.append(Doc(p.stem, text.splitlines()[0].lstrip("# ").strip(), text.strip()))
    return docs


@lru_cache(maxsize=1)
def _index():
    docs = load_docs()
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    return docs, vec, vec.fit_transform([d.title + "\n" + d.text for d in docs])


def search(query: str, k: int = 4) -> list[Doc]:
    docs, vec, mat = _index()
    sims = cosine_similarity(vec.transform([query]), mat)[0]
    return [docs[i] for i in sims.argsort()[::-1][:k] if sims[i] > 0]
