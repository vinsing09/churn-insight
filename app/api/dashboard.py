from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_account
from app.db.models import Account, AnalysisRun, Brief, Classification, Response, Theme
from app.db.session import get_db
from app.schemas import AnalysisRunOut, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    account_id = account.id

    total_responses = db.scalar(
        select(func.count(Response.id)).where(Response.account_id == account_id)
    ) or 0

    classified_responses = db.scalar(
        select(func.count(Classification.response_id))
        .join(Response, Response.id == Classification.response_id)
        .where(Response.account_id == account_id)
    ) or 0

    total_themes = db.scalar(
        select(func.count(Theme.id)).where(Theme.account_id == account_id)
    ) or 0

    active_themes = db.scalar(
        select(func.count(Theme.id))
        .where(Theme.account_id == account_id)
        .where(Theme.status == "active")
    ) or 0

    total_briefs = db.scalar(
        select(func.count(Brief.id)).where(Brief.account_id == account_id)
    ) or 0

    # Top primary reasons from classifications
    classifications = db.scalars(
        select(Classification)
        .join(Response, Response.id == Classification.response_id)
        .where(Response.account_id == account_id)
    ).all()

    reason_counter = Counter(c.primary_reason for c in classifications)
    top_primary_reasons = [
        {"reason": reason, "count": count}
        for reason, count in reason_counter.most_common(5)
    ]

    avg_intensity = (
        sum(c.emotional_intensity for c in classifications) / len(classifications)
        if classifications
        else None
    )

    competitor_pct = (
        sum(1 for c in classifications if c.competitor_mentioned) / len(classifications) * 100
        if classifications
        else None
    )

    latest_run = db.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account_id)
        .order_by(AnalysisRun.started_at.desc())
    ).first()

    return DashboardSummary(
        total_responses=total_responses,
        classified_responses=classified_responses,
        total_themes=total_themes,
        active_themes=active_themes,
        total_briefs=total_briefs,
        top_primary_reasons=top_primary_reasons,
        avg_emotional_intensity=avg_intensity,
        competitor_mention_pct=competitor_pct,
        latest_run=AnalysisRunOut.model_validate(latest_run) if latest_run else None,
    )
