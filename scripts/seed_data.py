from __future__ import annotations

import os
import random

from sqlalchemy.orm import Session

from data.database import make_engine, make_session_factory
from data.models import Base, User, Content, Skill, UserSkill, ContentSkill, Interaction

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./learning_reco.db")


def main():
    engine = make_engine(DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionFactory = make_session_factory(engine)

    rng = random.Random(42)

    skills = [
        "python", "sql", "statistics", "machine-learning", "fastapi",
        "docker", "git", "data-visualization", "nlp", "recommendation-systems"
    ]

    categories = [
        "python", "databases", "ml", "api", "devops", "data-science", "nlp"
    ]

    with SessionFactory() as db:
        skill_rows = []
        for s in skills:
            row = Skill(name=s)
            db.add(row)
            skill_rows.append(row)
        db.commit()

        # 20 content items
        content_rows = []
        for i in range(1, 21):
            cat = rng.choice(categories)
            title = f"{cat.upper()} Learning Module {i}"
            difficulty = rng.randint(1, 5)
            popularity = rng.random() * 0.6 + 0.2  # 0.2..0.8
            c = Content(title=title, category=cat, difficulty=difficulty, popularity=popularity)
            db.add(c)
            content_rows.append(c)
        db.commit()

        # map each content to 2-3 skills
        for c in content_rows:
            chosen = rng.sample(skill_rows, k=rng.randint(2, 3))
            for s in chosen:
                db.add(ContentSkill(content_id=c.id, skill_id=s.id))
        db.commit()

        # 10 users
        user_rows = []
        for u in range(1, 11):
            interests = rng.sample(categories, k=2)
            user = User(name=f"User {u}", interests=",".join(interests))
            db.add(user)
            user_rows.append(user)
        db.commit()

        # user skills
        for user in user_rows:
            chosen = rng.sample(skill_rows, k=3)
            for s in chosen:
                db.add(UserSkill(user_id=user.id, skill_id=s.id, proficiency=rng.randint(1, 5)))
        db.commit()

        # interactions (history) for most users
        for user in user_rows:
            n = rng.randint(0, 6)  # allow some cold-start users
            seen = rng.sample(content_rows, k=n) if n > 0 else []
            for c in seen:
                t = rng.choice(["view", "like", "complete"])
                rating = None
                if t in ("like", "complete"):
                    rating = float(rng.randint(3, 5))
                db.add(Interaction(user_id=user.id, content_id=c.id, type=t, rating=rating))
        db.commit()

    print("Seeded database:", DATABASE_URL)


if __name__ == "__main__":
    main()