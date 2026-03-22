import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_account
from app.db.models import Account, Brief, Classification, Response, Theme, ThemeResponse
from app.db.session import get_db
from app.schemas import BriefOut, GenerateBriefRequest
from app.services.brief import generate_brief

router = APIRouter(prefix="/briefs", tags=["briefs"])

_SAMPLE_SIZE = 8  # max responses sent to Claude for brief generation


@router.get("", response_model=list[BriefOut])
def list_briefs(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Brief)
        .where(Brief.account_id == account.id)
        .order_by(Brief.generated_at.desc())
    ).all()


@router.post("/generate", response_model=BriefOut, status_code=201)
async def generate_brief_endpoint(
    body: GenerateBriefRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    theme = db.scalars(
        select(Theme)
        .where(Theme.id == body.theme_id)
        .where(Theme.account_id == account.id)
    ).first()
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Fetch sample responses for context
    sample_responses = db.scalars(
        select(Response.text_stripped)
        .join(ThemeResponse, ThemeResponse.response_id == Response.id)
        .where(ThemeResponse.theme_id == theme.id)
        .order_by(ThemeResponse.relevance_score.desc())
        .limit(_SAMPLE_SIZE)
    ).all()

    brief_data = await generate_brief(
        theme_name=theme.name,
        theme_description=theme.description or "",
        sample_responses=list(sample_responses),
        ad_copy=account.ad_copy,
    )

    brief = Brief(
        id=str(uuid.uuid4()),
        account_id=account.id,
        theme_id=theme.id,
        generated_at=datetime.now(timezone.utc),
        **brief_data,
    )
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return brief


@router.get("/{brief_id}", response_model=BriefOut)
def get_brief(
    brief_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    brief = db.scalars(
        select(Brief)
        .where(Brief.id == brief_id)
        .where(Brief.account_id == account.id)
    ).first()
    if brief is None:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief
