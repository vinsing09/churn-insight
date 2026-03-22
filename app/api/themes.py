from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_account
from app.db.models import Account, Response, Theme, ThemeResponse
from app.db.session import get_db
from app.schemas import ResponseOut, ThemeOut

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=list[ThemeOut])
def list_themes(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Theme)
        .where(Theme.account_id == account.id)
        .order_by(Theme.priority_score.desc().nulls_last())
    ).all()


@router.get("/{theme_id}", response_model=ThemeOut)
def get_theme(
    theme_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    theme = db.scalars(
        select(Theme)
        .where(Theme.id == theme_id)
        .where(Theme.account_id == account.id)
    ).first()
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")
    return theme


@router.get("/{theme_id}/responses", response_model=list[ResponseOut])
def get_theme_responses(
    theme_id: str,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    theme = db.scalars(
        select(Theme)
        .where(Theme.id == theme_id)
        .where(Theme.account_id == account.id)
    ).first()
    if theme is None:
        raise HTTPException(status_code=404, detail="Theme not found")

    responses = db.scalars(
        select(Response)
        .join(ThemeResponse, ThemeResponse.response_id == Response.id)
        .where(ThemeResponse.theme_id == theme_id)
        .order_by(ThemeResponse.relevance_score.desc())
    ).all()
    return responses
