from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    Interview,
    Question,
    QuestionOption,
    QuestionRule,
    InterviewSession,
    InterviewAnswer,
)


def _get_answer_value(answers: dict[int, Any], question_id: int) -> Any:
    return answers.get(question_id)


def _evaluate_condition(cond: dict[str, Any] | None, answers: dict[int, Any], derived: dict[str, Any]) -> bool:
    if not cond:
        return False
    if "all" in cond:
        return all(_evaluate_condition(c, answers, derived) for c in cond["all"])
    if "any" in cond:
        return any(_evaluate_condition(c, answers, derived) for c in cond["any"])
    if "equals" in cond:
        data = cond["equals"]
        qid = int(data["questionId"]) if isinstance(data.get("questionId"), str) else data.get("questionId")
        return _get_answer_value(answers, qid) == data.get("value")
    if "gte" in cond:
        data = cond["gte"]
        left = derived.get(data.get("derived"))
        return (left is not None) and (left >= data.get("value"))
    return False


def _choose_next_by_rules(rules: list[QuestionRule], answers: dict[int, Any]) -> int | None | str:
    derived: dict[str, Any] = {}
    for rule in sorted(rules, key=lambda r: r.priority):
        if _evaluate_condition(rule.condition_json or None, answers, derived):
            action = rule.action_json or {}
            if action.get("end"):
                return "end"
            go_to = action.get("go_to")
            if go_to is not None:
                return int(go_to)
    return None


async def create_interview(db: AsyncSession, payload: dict[str, Any]) -> Interview:
    interview = Interview(name=payload["name"], description=payload.get("description"))
    db.add(interview)
    await db.flush()

    for q in payload["questions"]:
        question = Question(
            interview_id=interview.id,
            type=q["type"],
            prompt=q["prompt"],
            help_text=q.get("help_text"),
            required=q.get("required", True),
            order=q["order"],
            meta_json=q.get("meta"),
        )
        db.add(question)
        await db.flush()

        for opt in q.get("options", []) or []:
            db.add(QuestionOption(question_id=question.id, label=opt["label"], value=opt["value"]))

        for r in q.get("rules", []) or []:
            db.add(
                QuestionRule(
                    question_id=question.id,
                    priority=r.get("priority", 100),
                    condition_json=(r.get("condition") or None),
                    action_json=(r.get("action") or None),
                )
            )

    await db.commit()
    await db.refresh(interview)
    return interview


async def start_session(db: AsyncSession, interview_id: int, user_id: int | None = None) -> tuple[InterviewSession, Question | None]:
    first_question = (await db.execute(
        select(Question).where(Question.interview_id == interview_id).order_by(Question.order.asc()).limit(1)
    )).scalars().first()
    session = InterviewSession(interview_id=interview_id, user_id=user_id, status="active",
                               current_question_id=(first_question.id if first_question else None))
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session, first_question


async def get_next_question(db: AsyncSession, session_id: int) -> tuple[Question | None, bool]:
    session = await db.get(InterviewSession, session_id)
    if not session or session.status != "active":
        return None, True

    # If current question is set, return it
    if session.current_question_id:
        q = await db.get(Question, session.current_question_id)
        return q, False

    # Otherwise compute next based on last answered
    answers_list = (await db.execute(
        select(InterviewAnswer).where(InterviewAnswer.session_id == session_id)
    )).scalars().all()
    answers = {a.question_id: a.value_json for a in answers_list}

    # Find last answered question by max order
    last_q = None
    if answers:
        last_q = (await db.execute(
            select(Question)
            .where(Question.id.in_(list(answers.keys())))
            .order_by(Question.order.desc())
            .limit(1)
        )).scalars().first()

    if not last_q:
        first_question = (await db.execute(
            select(Question).where(Question.interview_id == session.interview_id).order_by(Question.order.asc()).limit(1)
        )).scalars().first()
        session.current_question_id = first_question.id if first_question else None
        await db.commit()
        return first_question, first_question is None

    # Apply rules
    next_by_rules = _choose_next_by_rules(last_q.rules or [], answers)
    if next_by_rules == "end":
        session.status = "completed"
        session.current_question_id = None
        await db.commit()
        return None, True
    if isinstance(next_by_rules, int):
        nq = await db.get(Question, next_by_rules)
        session.current_question_id = nq.id if nq else None
        await db.commit()
        return nq, nq is None

    # Fallback to next by order not yet answered
    next_q = (await db.execute(
        select(Question)
        .where(
            (Question.interview_id == session.interview_id)
        )
        .order_by(Question.order.asc())
    )).scalars().all()
    for q in next_q:
        if q.id not in answers:
            session.current_question_id = q.id
            await db.commit()
            return q, False

    session.status = "completed"
    session.current_question_id = None
    await db.commit()
    return None, True


async def submit_answer(db: AsyncSession, session_id: int, question_id: int, value: dict[str, Any] | None) -> tuple[Question | None, bool]:
    session = await db.get(InterviewSession, session_id)
    if not session or session.status != "active":
        return None, True

    db.add(InterviewAnswer(session_id=session_id, question_id=question_id, value_json=value or {}))
    session.current_question_id = None
    await db.commit()

    return await get_next_question(db, session_id)


