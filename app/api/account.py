from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_account
from app.db.models import Account
from app.db.session import get_db
from app.schemas import AccountOut, AccountUpdate, AdCopyUpdate

router = APIRouter(prefix="/account", tags=["account"])


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
