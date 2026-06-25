from __future__ import annotations

from typing import Iterable


def jaccard_similarity(a: Iterable[str], b: Iterable[str]) -> float:
    sa = {x.strip().lower() for x in a if x and x.strip()}
    sb = {x.strip().lower() for x in b if x and x.strip()}
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)