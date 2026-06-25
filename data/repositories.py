from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session, joinedload

from data.models import User, Content, Skill, UserSkill, ContentSkill, Interaction


def _split_csv(s: str) -> list[str]:
    if not s:
        return []
    return [x.strip().lower() for x in s.split(",") if x.strip()]


@dataclass(frozen=True)
class Repositories:
    users: "UserRepository"
    content: "ContentRepository"
    skills: "SkillRepository"
    interactions: "InteractionRepository"


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def list_users(self) -> list[User]:
        stmt = select(User).order_by(User.id)
        return list(self.db.scalars(stmt))

    def get_user_interests(self, user_id: int) -> list[str]:
        user = self.get(user_id)
        if not user:
            return []
        return _split_csv(user.interests)

    def get_user_skill_proficiencies(self, user_id: int) -> dict[int, int]:
        stmt = select(UserSkill).where(UserSkill.user_id == user_id)
        rows = list(self.db.scalars(stmt))
        return {r.skill_id: int(r.proficiency) for r in rows}

    def get_user_skills(self, user_id: int) -> list[Skill]:
        stmt = (
            select(Skill)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
            .order_by(Skill.name)
        )
        return list(self.db.scalars(stmt))

    def get_user_history(self, user_id: int, limit: int = 100) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .options(joinedload(Interaction.content))
            .where(Interaction.user_id == user_id)
            .order_by(desc(Interaction.created_at))
            .limit(limit)
        )
        return list(self.db.scalars(stmt))


class ContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, content_id: int) -> Optional[Content]:
        return self.db.get(Content, content_id)

    def list_all(self) -> list[Content]:
        stmt = select(Content).order_by(Content.id)
        return list(self.db.scalars(stmt))

    def list_top_popular(self, limit: int = 20) -> list[Content]:
        stmt = select(Content).order_by(desc(Content.popularity)).limit(limit)
        return list(self.db.scalars(stmt))

    def get_content_by_skill_ids(self, skill_ids: Iterable[int], limit: int = 50) -> list[Content]:
        skill_ids = list(skill_ids)
        if not skill_ids:
            return []
        stmt = (
            select(Content)
            .join(ContentSkill, ContentSkill.content_id == Content.id)
            .where(ContentSkill.skill_id.in_(skill_ids))
            .distinct()
            .order_by(desc(Content.popularity))
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def get_content_skills(self, content_id: int) -> list[Skill]:
        stmt = (
            select(Skill)
            .join(ContentSkill, ContentSkill.skill_id == Skill.id)
            .where(ContentSkill.content_id == content_id)
            .order_by(Skill.name)
        )
        return list(self.db.scalars(stmt))


class SkillRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Optional[Skill]:
        stmt = select(Skill).where(func.lower(Skill.name) == name.lower())
        return self.db.scalar(stmt)

    def list_all(self) -> list[Skill]:
        stmt = select(Skill).order_by(Skill.name)
        return list(self.db.scalars(stmt))


class InteractionRepository:
    def __init__(self, db: Session):
        self.db = db

    def record_interaction(
        self,
        user_id: int,
        content_id: int,
        interaction_type: str,
        rating: Optional[float] = None,
        created_at: Optional[datetime] = None,
    ) -> Interaction:
        it = Interaction(
            user_id=user_id,
            content_id=content_id,
            type=interaction_type,
            rating=rating,
            created_at=created_at or datetime.utcnow(),
        )
        self.db.add(it)
        self.db.commit()
        return it