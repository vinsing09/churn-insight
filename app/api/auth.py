import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.deps import get_current_account
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Account
from app.db.session import get_db
from app.schemas import AccountOut, LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

TRIAL_DAYS = 14


@router.post("/register", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalars(select(Account).where(Account.email == body.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    account = Account(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        plan="trial",
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=TRIAL_DAYS),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    account = db.scalars(select(Account).where(Account.email == body.email)).first()
    if not account or not verify_password(body.password, account.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(subject=account.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AccountOut)
def me(account: Account = Depends(get_current_account)):
    return account
