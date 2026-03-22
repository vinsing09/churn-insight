from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas import AccountOut, AccountUpdate, AdCopyUpdate

router = APIRouter(prefix="/account", tags=["account"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


class PlanOverrideRequest(BaseModel):
    account_id: str
    plan: str
    trial_days: Optional[int] = None


def _require_admin(x_admin_secret: str = Header(default="")) -> None:
    if x_admin_secret != settings.ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid or missing X-Admin-Secret")


@router.get("", response_model=AccountOut)
def get_account(account: Account = Depends(get_current_account)):
    return account


@router.put("", response_model=AccountOut)
def update_account(
    body: AccountUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    if body.plan is not None:
        account.plan = body.plan
    if body.stripe_customer_id is not None:
        account.stripe_customer_id = body.stripe_customer_id
    db.commit()
    db.refresh(account)
    return account


@admin_router.put("/account/plan", dependencies=[Depends(_require_admin)])
def admin_set_plan(body: PlanOverrideRequest, db: Session = Depends(get_db)):
    account = db.get(Account, body.account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    account.plan = body.plan
    if body.trial_days is not None:
        account.trial_ends_at = datetime.now(timezone.utc) + timedelta(days=body.trial_days)

    db.commit()
    return {"account_id": account.id, "email": account.email, "plan": account.plan, "updated": True}


@router.put("/ad-copy", response_model=AccountOut)
def update_ad_copy(
    body: AdCopyUpdate,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    account.ad_copy = body.ad_copy
    db.commit()
    db.refresh(account)
    return account
