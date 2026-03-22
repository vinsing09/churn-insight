"""Weekly analysis cron job using APScheduler."""
import logging
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import func, select

from app.db.models import Account, AnalysisRun, Brief, Integration, Response, Theme, ThemeResponse
from app.db.session import SessionLocal
from app.services.analysis import run_analysis
from app.services.email import send_weekly_digest

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")


async def weekly_analysis_job() -> None:
    """Run the full pipeline for every active account and send digest emails."""
    logger.info("Weekly analysis job started")
    db = SessionLocal()
    try:
        accounts = db.scalars(
            select(Account).where(Account.plan != "expired")
        ).all()
        logger.info("Processing %d account(s)", len(accounts))

        for account in accounts:
            # Skip accounts with no active integrations
            has_integration = db.scalars(
                select(Integration)
                .where(Integration.account_id == account.id)
                .where(Integration.is_active == True)  # noqa: E712
            ).first()
            if has_integration is None:
                logger.info("Skipping account %s — no active integrations", account.id)
                continue

            await _run_for_account(account, db)
    finally:
        db.close()
    logger.info("Weekly analysis job finished")


async def _run_for_account(account: Account, db) -> None:
    """Run analysis + send digest for one account. Errors are caught per-account."""
    account_id = account.id
    run = AnalysisRun(
        id=str(uuid.uuid4()),
        account_id=account_id,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    db.add(run)
    db.commit()

    try:
        await run_analysis(account_id=account_id, run_id=run.id, db=db)
        db.refresh(run)

        stats = _build_stats(account_id, run, db)
        send_weekly_digest(
            to_email=account.email,
            account_id=account_id,
            stats=stats,
        )
        logger.info(
            "Account %s: %d responses, %d themes, digest sent",
            account_id, run.responses_processed, run.themes_detected,
        )
    except Exception as exc:
        logger.exception("Analysis/digest failed for account %s: %s", account_id, exc)


def _build_stats(account_id: str, run: AnalysisRun, db) -> dict:
    """Collect stats for the digest email from the just-completed run."""
    total_responses = db.scalar(
        select(func.count(Response.id)).where(Response.account_id == account_id)
    ) or 0

    themes = db.scalars(
        select(Theme)
        .where(Theme.account_id == account_id)
        .where(Theme.status == "active")
        .order_by(Theme.priority_score.desc().nulls_last())
    ).all()

    # "New this week" = themes whose first_detected_at is within this run's window
    new_theme_names = [
        t.name for t in themes
        if t.first_detected_at >= run.started_at
    ]

    top_brief = db.scalars(
        select(Brief)
        .where(Brief.account_id == account_id)
        .order_by(Brief.priority_score.desc().nulls_last(), Brief.generated_at.desc())
    ).first()

    return {
        "new_responses": run.new_responses,
        "total_responses": total_responses,
        "themes": [
            {
                "name": t.name,
                "response_count": t.response_count,
                "priority_score": t.priority_score or 0.0,
            }
            for t in themes
        ],
        "new_themes": new_theme_names,
        "top_brief_headline": top_brief.headline_hypothesis if top_brief else None,
    }


def start_scheduler() -> None:
    """Register the weekly job and start the scheduler.

    Safe to call multiple times — skips start if already running.
    """
    if _scheduler.running:
        return

    _scheduler.add_job(
        weekly_analysis_job,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0, timezone="UTC"),
        id="weekly_analysis",
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1h late start (e.g. after a restart)
    )
    _scheduler.start()
    logger.info("Scheduler started — weekly job fires every Monday at 08:00 UTC")
