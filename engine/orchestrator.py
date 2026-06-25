from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.orm import Session

from data.repositories import Repositories, UserRepository, ContentRepository, SkillRepository, InteractionRepository
from data.models import Content
from engine.candidate_gen import CandidateGenerator
from engine.similarity import jaccard_similarity
from engine.scorer import Scorer, ScoreWeights


def _split_csv(s: str) -> list[str]:
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]


@dataclass
class RecommendationItem:
    content_id: int
    title: str
    category: str
    difficulty: int
    score: float
    explanation: str


class SimpleCache:
    def __init__(self, ttl_seconds: int = 30):
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str):
        row = self._store.get(key)
        if not row:
            return None
        ts, val = row
        if (time.time() - ts) > self.ttl_seconds:
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any):
        self._store[key] = (time.time(), value)

    def clear(self):
        self._store.clear()


class RecommendationOrchestrator:
    def __init__(
        self,
        cache_ttl_seconds: int = 30,
        weights: Optional[ScoreWeights] = None,
    ):
        self.candidates = CandidateGenerator()
        self.scorer = Scorer(weights or ScoreWeights())
        self.cache = SimpleCache(ttl_seconds=cache_ttl_seconds)

    def _repos(self, db: Session) -> Repositories:
        return Repositories(
            users=UserRepository(db),
            content=ContentRepository(db),
            skills=SkillRepository(db),
            interactions=InteractionRepository(db),
        )

    def get_recommendations(self, db: Session, user_id: int, limit: int = 10) -> dict[str, Any]:
        cache_key = f"reco:{user_id}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {"user_id": user_id, "cached": True, **cached}

        repos = self._repos(db)
        user = repos.users.get(user_id)
        if not user:
            raise KeyError(f"Unknown user_id={user_id}")

        history = repos.users.get_user_history(user_id, limit=200)
        seen_content_ids = {h.content_id for h in history}

        user_interests = _split_csv(user.interests)
        user_skills = repos.users.get_user_skills(user_id)
        user_skill_ids = [s.id for s in user_skills]

        # Determine a rough target difficulty from user proficiency average (1..5)
        profs = repos.users.get_user_skill_proficiencies(user_id).values()
        target_difficulty = None
        if profs:
            target_difficulty = sum(profs) / len(list(profs))

        # Strategy 1: skill-based candidates
        skill_candidates = repos.content.get_content_by_skill_ids(user_skill_ids, limit=100)

        # Strategy 2: popular fallback (also used for cold-start)
        popular_candidates = repos.content.list_top_popular(limit=50)

        # Strategy 3: interest/category match (using content.category vs interests tokens)
        # We'll implement as scoring signal; candidate set comes from merging.
        candidates = self.candidates.merge_dedup([skill_candidates, popular_candidates], limit=200)

        items: list[RecommendationItem] = []
        for c in candidates:
            if c.id in seen_content_ids:
                continue

            # compute skill_match: fraction of content skills that user has
            content_skills = repos.content.get_content_skills(c.id)
            content_skill_names = [s.name for s in content_skills]
            user_skill_names = [s.name for s in user_skills]
            skill_match = jaccard_similarity(user_skill_names, content_skill_names)

            # interest match: compare interests to category + title tokens
            content_tokens = [c.category] + c.title.split()
            interest_match = jaccard_similarity(user_interests, content_tokens)

            score = self.scorer.score(
                content=c,
                skill_match=skill_match,
                interest_match=interest_match,
                target_difficulty=target_difficulty,
            )

            explanation_parts = []
            if skill_match >= 0.34:
                explanation_parts.append("matches your skills")
            if interest_match >= 0.20:
                explanation_parts.append("aligns with your interests")
            if float(c.popularity) >= 0.7:
                explanation_parts.append("popular with other learners")
            explanation = ", ".join(explanation_parts) if explanation_parts else "recommended based on overall fit"

            items.append(
                RecommendationItem(
                    content_id=c.id,
                    title=c.title,
                    category=c.category,
                    difficulty=int(c.difficulty),
                    score=score,
                    explanation=explanation,
                )
            )

        # Cold-start: if no history and few skills, lean heavier on popularity + interests
        cold_start = (len(history) == 0)
        items.sort(key=lambda x: x.score, reverse=True)
        top = items[:limit]

        payload = {
            "cold_start": cold_start,
            "count": len(top),
            "recommendations": [i.__dict__ for i in top],
        }
        self.cache.set(cache_key, payload)
        return {"user_id": user_id, "cached": False, **payload}

    def record_feedback(
        self,
        db: Session,
        user_id: int,
        content_id: int,
        interaction_type: str,
        rating: Optional[float] = None,
    ) -> dict[str, Any]:
        repos = self._repos(db)
        if not repos.users.get(user_id):
            raise KeyError(f"Unknown user_id={user_id}")
        if not repos.content.get(content_id):
            raise KeyError(f"Unknown content_id={content_id}")

        # Record interaction
        repos.interactions.record_interaction(
            user_id=user_id,
            content_id=content_id,
            interaction_type=interaction_type,
            rating=rating,
        )

        # Invalidate cache for this user
        self.cache.clear()
        return {"ok": True}