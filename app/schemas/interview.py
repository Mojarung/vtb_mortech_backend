from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


QuestionType = Literal["text", "single_choice", "multi_choice", "scale", "date", "file"]


class QuestionOption(BaseModel):
    id: int | None = None
    label: str
    value: str

    model_config = {
        "from_attributes": True
    }


class RuleCondition(BaseModel):
    all: list["RuleCondition"] | None = None
    any: list["RuleCondition"] | None = None
    equals: dict[str, Any] | None = None
    gte: dict[str, Any] | None = None

    model_config = {
        "from_attributes": True
    }


class RuleAction(BaseModel):
    go_to: int | None = Field(default=None, description="ID of the next question")
    end: bool | None = None

    model_config = {
        "from_attributes": True
    }


class QuestionRule(BaseModel):
    id: int | None = None
    priority: int = 100
    condition: RuleCondition | None = None
    action: RuleAction | None = None

    model_config = {
        "from_attributes": True
    }


class Question(BaseModel):
    id: int | None = None
    type: QuestionType
    prompt: str
    help_text: str | None = None
    required: bool = True
    order: int
    meta: dict[str, Any] | None = None
    options: list[QuestionOption] | None = None
    rules: list[QuestionRule] | None = None

    model_config = {
        "from_attributes": True
    }


class InterviewCreate(BaseModel):
    name: str
    description: str | None = None
    questions: list[Question]


class InterviewOut(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    questions: list[Question]

    model_config = {
        "from_attributes": True
    }


class SessionStartOut(BaseModel):
    session_id: int
    question: Question | None


class NextQuestionOut(BaseModel):
    question: Question | None
    completed: bool


class SubmitAnswerIn(BaseModel):
    question_id: int
    value: dict[str, Any] | None = None


class SubmitAnswerOut(BaseModel):
    next: Question | None
    completed: bool


