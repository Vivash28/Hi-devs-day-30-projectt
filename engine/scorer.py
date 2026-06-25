from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from data.models import Content


@dataclass
class ScoreWeights:
    skill_match: float = 0.45
    interest_match: float = 0.25
    popularity: float = 0.20
    difficulty_match: float = 0.10


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class Scorer:
    weights: ScoreWeights

    def score(
        self,
        content: Content,
        skill_match: float,
        interest_match: float,
        target_difficulty: Optional[float],
    ) -> float:
        # popularity assumed 0..1-ish; clamp for safety
        pop = clamp(float(content.popularity))

        diff_match = 0.5
        if target_difficulty is not None:
            # distance-based match (1..5)
            dist = abs(float(content.difficulty) - float(target_difficulty))
            diff_match = clamp(1.0 - (dist / 4.0))  # 0..1

        w = self.weights
        total = (
            w.skill_match * clamp(skill_match)
            + w.interest_match * clamp(interest_match)
            + w.popularity * pop
            + w.difficulty_match * clamp(diff_match)
        )
        return float(total)