from __future__ import annotations

import os

from data.database import make_engine, make_session_factory
from data.models import Base, User, Content


def test_database_tables_create():
    engine = make_engine("sqlite:///./test_learning_reco.db")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionFactory = make_session_factory(engine)

    with SessionFactory() as db:
        db.add(User(name="Alice", interests="python,ml"))
        db.add(Content(title="Intro to Python", category="python", difficulty=1, popularity=0.9))
        db.commit()

        assert db.query(User).count() == 1
        assert db.query(Content).count() == 1