import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_account
from app.db.models import Account, AnalysisRun
from app.db.session import get_db, SessionLocal
from app.schemas import AnalysisRunOut
from app.services.analysis import run_analysis

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisRunOut, status_code=202)
def trigger_analysis(
    background_tasks: BackgroundTasks,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    # Prevent concurrent runs
    active = db.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account.id)
        .where(AnalysisRun.status == "running")
    ).first()
    if active:
        raise HTTPException(status_code=409, detail="An analysis run is already in progress")

    run = AnalysisRun(
        id=str(uuid.uuid4()),
        account_id=account.id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Background task uses its own DB session so it outlives the request
    background_tasks.add_task(_run_in_background, account.id, run.id)
    return run


@router.get("/status", response_model=AnalysisRunOut | None)
def get_status(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    run = db.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account.id)
        .order_by(AnalysisRun.started_at.desc())
    ).first()
    return run


@router.get("/runs", response_model=list[AnalysisRunOut])
def list_runs(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account.id)
        .order_by(AnalysisRun.started_at.desc())
    ).all()


async def _run_in_background(account_id: str, run_id: str) -> None:
    """Open a fresh session for the background task."""
    db = SessionLocal()
    try:
        await run_analysis(account_id=account_id, run_id=run_id, db=db)
    finally:
        db.close()
