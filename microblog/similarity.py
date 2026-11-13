"""Related posts and search, from a small TF-IDF index written from scratch.

Each post becomes a vector of word weights: words frequent in that post but
rare across the blog weigh the most (TF-IDF). Related posts are the nearest
vectors by cosine similarity; search scores posts against the query the same
way, with the title counted twice.

Built in memory per request; plenty fast for a personal blog's few hundred
posts, and no dependency heavier than the standard library.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

_WORD = re.compile(r"[a-z0-9][a-z0-9'+#.-]*[a-z0-9+#]|[a-z0-9]")
STOP = set(
    "a an and are as at be but by for from has have i if in into is it its of on or our so that the their them then "
    "there these they this to was we were what when which who will with you your my me not no can do did just than "
    "too very about after again all also any been before being both each few more most other over same some such "
    "only own out up down off how why where here".split()
)


def tokens(text: str) -> list[str]:
    words = (w.strip(".'-") for w in _WORD.findall(text.lower()))
    return [w[:-1] if w.endswith("s") and len(w) > 4 else w for w in words if w and w not in STOP]


class Index:
    def __init__(self, docs: Iterable[tuple[int, str, str]]):
        """docs: (id, title, body)."""
        self.ids: list[int] = []
        counts: list[Counter] = []
        for doc_id, title, body in docs:
            self.ids.append(doc_id)
            counts.append(Counter(tokens(title) * 2 + tokens(body)))
        n = len(counts)
        df = Counter(term for c in counts for term in c)
        self.idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
        self.vectors = [self._weigh(c) for c in counts]

    def _weigh(self, counts: Counter) -> dict[str, float]:
        vec = {t: (1 + math.log(c)) * self.idf.get(t, 0.0) for t, c in counts.items()}
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {t: v / norm for t, v in vec.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(t, 0.0) for t, v in a.items())

    def related(self, doc_id: int, k: int = 3, min_score: float = 0.05) -> list[tuple[int, float]]:
        if doc_id not in self.ids:
            return []
        me = self.vectors[self.ids.index(doc_id)]
        scored = [(other, self._cosine(me, vec)) for other, vec in zip(self.ids, self.vectors, strict=True)]
        scored = [(i, s) for i, s in scored if i != doc_id and s >= min_score]
        return sorted(scored, key=lambda x: -x[1])[:k]

    def search(self, query: str, k: int = 20) -> list[tuple[int, float]]:
        q = self._weigh(Counter(t for t in tokens(query) if t in self.idf))
        scored = [(i, self._cosine(q, vec)) for i, vec in zip(self.ids, self.vectors, strict=True)]
        return sorted([(i, s) for i, s in scored if s > 0], key=lambda x: -x[1])[:k]
