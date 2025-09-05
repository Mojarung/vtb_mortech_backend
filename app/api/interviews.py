from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.interview import Question

from app.db.session import get_db
from app.models.interview import Interview
from app.schemas.interview import (
    InterviewCreate,
    InterviewOut,
    SessionStartOut,
    NextQuestionOut,
    SubmitAnswerIn,
    SubmitAnswerOut,
)
from app.services import interview_service as svc


router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("", response_model=InterviewOut)
async def create_interview(payload: InterviewCreate, db: AsyncSession = Depends(get_db)):
    interview = await svc.create_interview(db, payload.model_dump())
    # Reload with relationships eagerly to avoid async lazy loads during serialization
    stmt = (
        select(Interview)
        .where(Interview.id == interview.id)
        .options(
            selectinload(Interview.questions).options(
                selectinload(Question.options),
                selectinload(Question.rules),
            )
        )
    )
    fresh = (await db.execute(stmt)).scalars().first()
    return fresh


@router.get("/{interview_id}", response_model=InterviewOut)
async def get_interview(interview_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Interview)
        .where(Interview.id == interview_id)
        .options(
            selectinload(Interview.questions).options(
                selectinload(Question.options),
                selectinload(Question.rules),
            )
        )
    )
    interview = (await db.execute(stmt)).scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


@router.post("/{interview_id}/sessions", response_model=SessionStartOut)
async def start_session(interview_id: int, db: AsyncSession = Depends(get_db)):
    session, question = await svc.start_session(db, interview_id)
    if question:
        stmt_q = (
            select(Question)
            .where(Question.id == question.id)
            .options(
                selectinload(Question.options),
                selectinload(Question.rules),
            )
        )
        question = (await db.execute(stmt_q)).scalars().first()
    return SessionStartOut(session_id=session.id, question=question)


@router.get("/sessions/{session_id}/next", response_model=NextQuestionOut)
async def get_next(session_id: int, db: AsyncSession = Depends(get_db)):
    question, completed = await svc.get_next_question(db, session_id)
    if question:
        stmt_q = (
            select(Question)
            .where(Question.id == question.id)
            .options(
                selectinload(Question.options),
                selectinload(Question.rules),
            )
        )
        question = (await db.execute(stmt_q)).scalars().first()
    return NextQuestionOut(question=question, completed=completed)


@router.post("/sessions/{session_id}/answers", response_model=SubmitAnswerOut)
async def submit_answer(session_id: int, body: SubmitAnswerIn, db: AsyncSession = Depends(get_db)):
    next_q, completed = await svc.submit_answer(db, session_id, body.question_id, body.value)
    if next_q:
        stmt_q = (
            select(Question)
            .where(Question.id == next_q.id)
            .options(
                selectinload(Question.options),
                selectinload(Question.rules),
            )
        )
        next_q = (await db.execute(stmt_q)).scalars().first()
    return SubmitAnswerOut(next=next_q, completed=completed)


