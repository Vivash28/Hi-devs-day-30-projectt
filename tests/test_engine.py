from __future__ import annotations

from data.database import make_engine, make_session_factory
from data.models import Base, User, Content, Skill, UserSkill, ContentSkill
from engine.orchestrator import RecommendationOrchestrator


def test_orchestrator_recommendations_cold_start():
    engine = make_engine("sqlite:///./test_engine.db")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionFactory = make_session_factory(engine)

    with SessionFactory() as db:
        # Seed minimal
        u = User(name="Bob", interests="python,api")
        db.add(u)
        s1 = Skill(name="python")
        s2 = Skill(name="fastapi")
        db.add_all([s1, s2])
        db.commit()

        db.add(UserSkill(user_id=u.id, skill_id=s1.id, proficiency=2))
        db.commit()

        c1 = Content(title="FASTAPI Module", category="api", difficulty=2, popularity=0.8)
        c2 = Content(title="SQL Module", category="databases", difficulty=2, popularity=0.7)
        db.add_all([c1, c2])
        db.commit()

        db.add(ContentSkill(content_id=c1.id, skill_id=s2.id))
        db.commit()

        orch = RecommendationOrchestrator(cache_ttl_seconds=0)
        rec = orch.get_recommendations(db=db, user_id=u.id, limit=5)

        assert rec["user_id"] == u.id
        assert rec["count"] >= 1
        assert isinstance(rec["recommendations"], list)