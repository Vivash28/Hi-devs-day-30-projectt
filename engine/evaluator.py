from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


def precision_at_k(recommended: Sequence[int], relevant: set[int], k: int = 5) -> float:
    rec_k = list(recommended)[:k]
    if not rec_k:
        return 0.0
    hits = sum(1 for x in rec_k if x in relevant)
    return hits / k


def recall_at_k(recommended: Sequence[int], relevant: set[int], k: int = 5) -> float:
    if not relevant:
        return 0.0
    rec_k = list(recommended)[:k]
    hits = sum(1 for x in rec_k if x in relevant)
    return hits / len(relevant)


def ndcg_at_k(recommended: Sequence[int], relevant: set[int], k: int = 5) -> float:
    rec_k = list(recommended)[:k]

    def dcg(items: Sequence[int]) -> float:
        s = 0.0
        for i, item in enumerate(items, start=1):
            rel = 1.0 if item in relevant else 0.0
            s += (2**rel - 1.0) / math.log2(i + 1)
        return s

    ideal = [1] * min(k, len(relevant))
    idcg = sum((2**1 - 1.0) / math.log2(i + 1) for i in range(1, len(ideal) + 1))
    if idcg == 0:
        return 0.0
    return dcg(rec_k) / idcg


@dataclass
class EvalResult:
    precision5: float
    recall5: float
    ndcg5: float