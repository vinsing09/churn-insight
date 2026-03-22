"""End-to-end pipeline runner: classify → embed → cluster → themes → briefs.

Usage:
    python scripts/run_pipeline.py
"""
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import anthropic  # noqa: F401 — imported to confirm key works before spending $
from rich.console import Console
from rich.table import Table
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Account, AnalysisRun, Brief, Theme, ThemeResponse, Response
from app.db.session import SessionLocal
from app.services.analysis import run_analysis
from app.services.brief import generate_brief

ACCOUNT_EMAIL = "vineet.singh1208@gmail.com"
AD_COPY = (
    "The most powerful project management tool. "
    "Built for teams who move fast. "
    "Advanced features for serious teams."
)

console = Console()


def _check_keys() -> None:
    missing = []
    if not settings.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not settings.OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if missing:
        console.print(f"[red]ERROR:[/red] Missing env vars: {', '.join(missing)}")
        console.print("Add them to your .env file and retry.")
        sys.exit(1)


async def main() -> None:
    _check_keys()
    db = SessionLocal()
    try:
        # ── Resolve account ───────────────────────────────────────────────────
        account = db.scalars(
            select(Account).where(Account.email == ACCOUNT_EMAIL)
        ).first()
        if account is None:
            console.print(f"[red]Account not found:[/red] {ACCOUNT_EMAIL}")
            sys.exit(1)

        account_id = account.id
        console.print(f"\n[bold]Account:[/bold] {account.email} ({account_id})")

        # ── Count seeded responses ────────────────────────────────────────────
        total_responses = db.scalars(
            select(Response).where(Response.account_id == account_id)
        ).all()
        console.print(f"[bold]Responses in DB:[/bold] {len(total_responses)}")
        if not total_responses:
            console.print("[yellow]No responses found — run seed_test_data.py first[/yellow]")
            sys.exit(1)

        # ── Save ad copy ──────────────────────────────────────────────────────
        account.ad_copy = AD_COPY
        db.commit()
        console.print("[bold]Ad copy:[/bold] saved ✓")

        # ── Create analysis run record ────────────────────────────────────────
        run = AnalysisRun(
            id=str(uuid.uuid4()),
            account_id=account_id,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        console.print(f"\n[bold cyan]▶ Running analysis pipeline (run {run.id[:8]}…)[/bold cyan]")

        # ── Run classify → embed → cluster → themes ───────────────────────────
        await run_analysis(account_id=account_id, run_id=run.id, db=db)
        db.refresh(run)

        console.print(f"\n[bold green]✓ Analysis complete[/bold green]")
        console.print(f"  Responses processed : {run.responses_processed}")
        console.print(f"  New classifications : {run.new_responses}")
        console.print(f"  Themes detected     : {run.themes_detected}")
        console.print(f"  Status              : {run.status}")
        if run.error_message:
            console.print(f"  [red]Error:[/red] {run.error_message}")

        # ── Print themes table ────────────────────────────────────────────────
        themes = db.scalars(
            select(Theme)
            .where(Theme.account_id == account_id)
            .where(Theme.status == "active")
            .order_by(Theme.priority_score.desc().nulls_last())
        ).all()

        if themes:
            t = Table(title="\nThemes detected", show_lines=True)
            t.add_column("Name", style="bold")
            t.add_column("Responses", justify="right")
            t.add_column("Avg intensity", justify="right")
            t.add_column("Competitor %", justify="right")
            t.add_column("Priority", justify="right")
            for theme in themes:
                t.add_row(
                    theme.name,
                    str(theme.response_count),
                    f"{theme.avg_emotional_intensity:.1f}" if theme.avg_emotional_intensity else "—",
                    f"{theme.competitor_mention_pct:.0f}%" if theme.competitor_mention_pct is not None else "—",
                    f"{theme.priority_score:.2f}" if theme.priority_score else "—",
                )
            console.print(t)
        else:
            console.print("[yellow]No active themes found after clustering[/yellow]")
            return

        # ── Generate briefs for each theme ────────────────────────────────────
        console.print("\n[bold cyan]▶ Generating ad creative briefs…[/bold cyan]")
        generated = []
        for theme in themes:
            sample_texts = db.scalars(
                select(Response.text_stripped)
                .join(ThemeResponse, ThemeResponse.response_id == Response.id)
                .where(ThemeResponse.theme_id == theme.id)
                .limit(8)
            ).all()

            brief_data = await generate_brief(
                theme_name=theme.name,
                theme_description=theme.description or "",
                sample_responses=list(sample_texts),
                ad_copy=account.ad_copy,
            )

            brief = Brief(
                id=str(uuid.uuid4()),
                account_id=account_id,
                theme_id=theme.id,
                generated_at=datetime.now(timezone.utc),
                **brief_data,
            )
            db.add(brief)
            db.commit()
            generated.append(brief)
            console.print(f"  [green]✓[/green] {theme.name} → [italic]{brief.angle_name}[/italic]")

        # ── Final briefs table ────────────────────────────────────────────────
        bt = Table(title="\nGenerated briefs", show_lines=True)
        bt.add_column("Theme", style="bold")
        bt.add_column("Angle")
        bt.add_column("Headline hypothesis")
        for b in generated:
            theme_name = next((th.name for th in themes if th.id == b.theme_id), "?")
            bt.add_row(theme_name, b.angle_name, b.headline_hypothesis)
        console.print(bt)
        console.print(f"\n[bold green]✓ Done.[/bold green] {len(generated)} brief(s) generated.")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
