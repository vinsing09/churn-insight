"""Integration management: Typeform OAuth and Delighted API key."""
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_account
from app.core.security import encrypt_text
from app.db.models import Account, Integration
from app.db.session import get_db
from app.schemas import DelightedConnectRequest, IntegrationOut

router = APIRouter(prefix="/integrations", tags=["integrations"])

TYPEFORM_AUTH_URL = "https://api.typeform.com/oauth/authorize"
TYPEFORM_TOKEN_URL = "https://api.typeform.com/oauth/token"


@router.get("", response_model=list[IntegrationOut])
def list_integrations(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Integration).where(Integration.account_id == account.id)
    ).all()


@router.post("/typeform/connect")
def typeform_connect(account: Account = Depends(get_current_account)):
    """Return the Typeform OAuth authorisation URL for the frontend to redirect to."""
    params = {
        "client_id": settings.TYPEFORM_CLIENT_ID,
        "redirect_uri": settings.TYPEFORM_REDIRECT_URI,
        "scope": "responses:read forms:read",
        "state": account.id,  # simple CSRF token — use a signed value in production
    }
    return {"auth_url": f"{TYPEFORM_AUTH_URL}?{urlencode(params)}"}


@router.get("/typeform/callback")
async def typeform_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """Exchange the OAuth code for tokens and persist the integration."""
    import httpx

    account = db.get(Account, state)
    if account is None:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            TYPEFORM_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.TYPEFORM_REDIRECT_URI,
                "client_id": settings.TYPEFORM_CLIENT_ID,
                "client_secret": settings.TYPEFORM_CLIENT_SECRET,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Typeform token exchange failed")

    tokens = resp.json()
    _upsert_integration(
        db=db,
        account_id=account.id,
        source="typeform",
        access_token=tokens.get("access_token", ""),
        refresh_token=tokens.get("refresh_token"),
    )

    return RedirectResponse(url=f"{settings.FRONTEND_URL}/integrations?connected=typeform")


@router.post("/typeform/sync")
async def typeform_sync(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Trigger a Typeform response sync for the authenticated account."""
    integration = _get_integration(db, account.id, "typeform")
    # TODO: call TypeformClient.fetch_responses() and upsert Response records
    integration.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "typeform sync triggered", "integration_id": integration.id}


@router.post("/delighted/connect", response_model=IntegrationOut)
def delighted_connect(
    body: DelightedConnectRequest,
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Store a Delighted API key for the account."""
    integration = _upsert_integration(
        db=db,
        account_id=account.id,
        source="delighted",
        access_token=body.api_key,
    )
    return integration


@router.post("/delighted/sync")
async def delighted_sync(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Trigger a Delighted survey response sync."""
    integration = _get_integration(db, account.id, "delighted")
    # TODO: call DelightedClient.fetch_survey_responses() and upsert Response records
    integration.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "delighted sync triggered", "integration_id": integration.id}


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_integration(db: Session, account_id: str, source: str) -> Integration:
    integration = db.scalars(
        select(Integration)
        .where(Integration.account_id == account_id)
        .where(Integration.source == source)
        .where(Integration.is_active == True)  # noqa: E712
    ).first()
    if integration is None:
        raise HTTPException(status_code=404, detail=f"{source} integration not connected")
    return integration


def _upsert_integration(
    db: Session,
    account_id: str,
    source: str,
    access_token: str,
    refresh_token: str | None = None,
) -> Integration:
    integration = db.scalars(
        select(Integration)
        .where(Integration.account_id == account_id)
        .where(Integration.source == source)
    ).first()

    encrypted_access = encrypt_text(access_token) if settings.ENCRYPTION_KEY else access_token
    encrypted_refresh = encrypt_text(refresh_token) if (refresh_token and settings.ENCRYPTION_KEY) else refresh_token

    if integration is None:
        integration = Integration(
            id=str(uuid.uuid4()),
            account_id=account_id,
            source=source,
            access_token_encrypted=encrypted_access,
            refresh_token_encrypted=encrypted_refresh,
            is_active=True,
        )
        db.add(integration)
    else:
        integration.access_token_encrypted = encrypted_access
        integration.refresh_token_encrypted = encrypted_refresh
        integration.is_active = True

    db.commit()
    db.refresh(integration)
    return integration
