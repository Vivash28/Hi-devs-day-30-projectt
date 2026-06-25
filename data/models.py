from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Float,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    interests = Column(String, nullable=False, default="")  # comma-separated
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="user", cascade="all, delete-orphan")
    user_skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)  # 1..5
    popularity = Column(Float, nullable=False, default=0.0)  # 0..1-ish

    interactions = relationship("Interaction", back_populates="content", cascade="all, delete-orphan")
    content_skills = relationship("ContentSkill", back_populates="content", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_content_category", "category"),
        Index("ix_content_popularity", "popularity"),
    )


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
    content_skills = relationship("ContentSkill", back_populates="skill", cascade="all, delete-orphan")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)
    proficiency = Column(Integer, nullable=False, default=1)  # 1..5

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
    )


class ContentSkill(Base):
    __tablename__ = "content_skills"

    content_id = Column(Integer, ForeignKey("content.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)

    content = relationship("Content", back_populates="content_skills")
    skill = relationship("Skill", back_populates="content_skills")

    __table_args__ = (
        UniqueConstraint("content_id", "skill_id", name="uq_content_skill"),
    )


class Interaction(Base):
    __tablename__ = "interactions"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    content_id = Column(Integer, ForeignKey("content.id"), primary_key=True)
    type = Column(String, nullable=False)  # view / like / complete / dislike
    rating = Column(Float, nullable=True)  # optional 1..5
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="interactions")
    content = relationship("Content", back_populates="interactions")

    __table_args__ = (
        Index("ix_interactions_user_created", "user_id", "created_at"),
    )