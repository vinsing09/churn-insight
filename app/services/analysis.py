"""End-to-end analysis pipeline: classify → embed → cluster → themes."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRun, Classification, Response, Theme, ThemeResponse
from app.services import classify as svc_classify
from app.services import cluster as svc_cluster
from app.services import embeddings as svc_embeddings


async def run_analysis(account_id: str, run_id: str, db: Session) -> None:
    """Full analysis pipeline. Called as a background task.

    Steps:
    1. Classify unclassified responses with Claude Haiku.
    2. Embed ALL classified responses with OpenAI.
    3. Cluster embeddings with HDBSCAN.
    4. Create / refresh Theme + ThemeResponse records.
    5. Mark the AnalysisRun as completed.
    """
    run = db.get(AnalysisRun, run_id)
    if run is None:
        return

    try:
        # ── 1. Classify unclassified responses ────────────────────────────────
        unclassified = db.scalars(
            select(Response)
            .where(Response.account_id == account_id)
            .where(
                ~Response.id.in_(
                    select(Classification.response_id)
                )
            )
        ).all()

        new_count = 0
        for resp in unclassified:
            classification_data = await svc_classify.classify_response(resp.text_stripped)
            db.add(Classification(response_id=resp.id, **classification_data))
            new_count += 1

        db.commit()
        run.responses_processed = len(unclassified)
        run.new_responses = new_count
        db.commit()

        # ── 2. Embed all classified responses ─────────────────────────────────
        classified_responses = db.scalars(
            select(Response)
            .where(Response.account_id == account_id)
            .join(Classification)
        ).all()

        if not classified_responses:
            _finish_run(run, db, themes_detected=0)
            return

        texts = [r.text_stripped for r in classified_responses]
        response_ids = [r.id for r in classified_responses]

        embeddings = await svc_embeddings.embed_texts(texts)
        svc_embeddings.save_embeddings(account_id, response_ids, embeddings)

        # ── 3. Cluster ────────────────────────────────────────────────────────
        labels = svc_cluster.cluster_embeddings(embeddings)
        cluster_map = svc_cluster.labels_to_cluster_map(labels, response_ids)

        # ── 4. Refresh themes ─────────────────────────────────────────────────
        now = datetime.now(timezone.utc)

        # Mark all existing themes as declining before refresh
        existing_themes = db.scalars(
            select(Theme).where(Theme.account_id == account_id)
        ).all()
        for t in existing_themes:
            t.status = "declining"
            t.last_updated_at = now
        db.commit()

        themes_detected = 0
        for cluster_label, cluster_response_ids in cluster_map.items():
            _upsert_theme(
                account_id=account_id,
                cluster_label=cluster_label,
                cluster_response_ids=cluster_response_ids,
                all_responses={r.id: r for r in classified_responses},
                db=db,
                now=now,
            )
            themes_detected += 1

        db.commit()
        _finish_run(run, db, themes_detected=themes_detected)

    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise


def _upsert_theme(
    account_id: str,
    cluster_label: int,
    cluster_response_ids: list[str],
    all_responses: dict[str, Response],
    db: Session,
    now: datetime,
) -> None:
    """Create or update a Theme for one HDBSCAN cluster."""
    # Use a stable deterministic name based on cluster label and account
    # (real implementation would use Claude to name themes)
    theme_name = f"Theme {cluster_label + 1}"

    # Look for existing theme by name for this account
    theme = db.scalars(
        select(Theme)
        .where(Theme.account_id == account_id)
        .where(Theme.name == theme_name)
    ).first()

    if theme is None:
        theme = Theme(
            id=str(uuid.uuid4()),
            account_id=account_id,
            name=theme_name,
            description=None,
            first_detected_at=now,
            last_updated_at=now,
            status="active",
        )
        db.add(theme)
    else:
        theme.status = "active"
        theme.last_updated_at = now

    # Recalculate aggregate stats from classifications
    responses_in_cluster = [all_responses[rid] for rid in cluster_response_ids if rid in all_responses]
    classifications = [r.classification for r in responses_in_cluster if r.classification]

    theme.response_count = len(cluster_response_ids)

    if classifications:
        theme.avg_emotional_intensity = sum(c.emotional_intensity for c in classifications) / len(classifications)
        competitor_count = sum(1 for c in classifications if c.competitor_mentioned)
        theme.competitor_mention_pct = competitor_count / len(classifications) * 100
        # Priority score = emotional_intensity × actionability weight
        actionability_weights = {"high": 1.0, "medium": 0.6, "low": 0.2}
        theme.priority_score = (
            theme.avg_emotional_intensity
            * sum(actionability_weights.get(c.marketing_actionability, 0.5) for c in classifications)
            / len(classifications)
        )

    db.flush()  # get theme.id

    # Replace ThemeResponse entries for this theme
    existing = db.scalars(
        select(ThemeResponse).where(ThemeResponse.theme_id == theme.id)
    ).all()
    for tr in existing:
        db.delete(tr)
    db.flush()

    for rid in cluster_response_ids:
        db.add(ThemeResponse(theme_id=theme.id, response_id=rid, relevance_score=1.0))


def _finish_run(run: AnalysisRun, db: Session, themes_detected: int) -> None:
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    run.themes_detected = themes_detected
    db.commit()
