from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="interview", cascade="all, delete-orphan", order_by="Question.order"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, single_choice, multi_choice, scale, date, file
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    meta_json: Mapped[dict[str, Any] | None] = mapped_column(SQLITE_JSON, nullable=True)

    interview: Mapped[Interview] = relationship("Interview", back_populates="questions")
    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption", back_populates="question", cascade="all, delete-orphan"
    )
    rules: Mapped[list["QuestionRule"]] = relationship(
        "QuestionRule", back_populates="question", cascade="all, delete-orphan", order_by="QuestionRule.priority"
    )


class QuestionOption(Base):
    __tablename__ = "question_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    question: Mapped[Question] = relationship("Question", back_populates="options")


class QuestionRule(Base):
    __tablename__ = "question_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False, index=True)
    condition_json: Mapped[dict[str, Any] | None] = mapped_column(SQLITE_JSON, nullable=True)
    action_json: Mapped[dict[str, Any] | None] = mapped_column(SQLITE_JSON, nullable=True)

    question: Mapped[Question] = relationship("Question", back_populates="rules")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, completed, abandoned
    current_question_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    value_json: Mapped[dict[str, Any] | None] = mapped_column(SQLITE_JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


