from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from data.models import Content


@dataclass
class CandidateGenerator:
    """
    Generates candidate content ids given:
    - user skills
    - user interests
    - fallback popular content
    """

    def by_skills(self, content_by_skills: list[Content]) -> list[Content]:
        return content_by_skills

    def by_popularity(self, popular: list[Content]) -> list[Content]:
        return popular

    def merge_dedup(self, lists: Iterable[list[Content]], limit: int = 200) -> list[Content]:
        seen: set[int] = set()
        out: list[Content] = []
        for lst in lists:
            for c in lst:
                if c.id in seen:
                    continue
                seen.add(c.id)
                out.append(c)
                if len(out) >= limit:
                    return out
        return out