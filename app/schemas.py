from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AccountOut(BaseModel):
    id: str
    email: str
    plan: str
    created_at: datetime
    trial_ends_at: Optional[datetime]
    ad_copy: Optional[str]
    stripe_customer_id: Optional[str]

    model_config = {"from_attributes": True}


# ── Account ───────────────────────────────────────────────────────────────────

class AccountUpdate(BaseModel):
    plan: Optional[str] = None
    stripe_customer_id: Optional[str] = None


class AdCopyUpdate(BaseModel):
    ad_copy: str


# ── Integrations ──────────────────────────────────────────────────────────────

class IntegrationOut(BaseModel):
    id: str
    source: str
    is_active: bool
    last_synced_at: Optional[datetime]
    metadata_json: Optional[dict]

    model_config = {"from_attributes": True}


class DelightedConnectRequest(BaseModel):
    api_key: str


class TypeformConnectRequest(BaseModel):
    # Called after OAuth; client passes the code here or we read it from the callback
    pass


# ── Analysis ──────────────────────────────────────────────────────────────────

class AnalysisRunOut(BaseModel):
    id: str
    started_at: datetime
    completed_at: Optional[datetime]
    responses_processed: int
    new_responses: int
    themes_detected: int
    status: str
    error_message: Optional[str]

    model_config = {"from_attributes": True}


# ── Classifications ───────────────────────────────────────────────────────────

class ClassificationOut(BaseModel):
    primary_reason: str
    competitor_mentioned: bool
    competitor_name: Optional[str]
    emotional_intensity: int
    marketing_actionability: str
    key_phrases: Optional[list[str]]
    summary: str
    classified_at: datetime
    model_used: str
    confidence: float

    model_config = {"from_attributes": True, "protected_namespaces": ()}


# ── Responses ─────────────────────────────────────────────────────────────────

class ResponseOut(BaseModel):
    id: str
    source: str
    response_date: Optional[datetime]
    text_stripped: str
    classification: Optional[ClassificationOut]

    model_config = {"from_attributes": True}


# ── Themes ────────────────────────────────────────────────────────────────────

class ThemeOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    response_count: int
    avg_emotional_intensity: Optional[float]
    competitor_mention_pct: Optional[float]
    priority_score: Optional[float]
    first_detected_at: datetime
    last_updated_at: datetime
    status: str

    model_config = {"from_attributes": True}


# ── Briefs ────────────────────────────────────────────────────────────────────

class BriefOut(BaseModel):
    id: str
    theme_id: str
    angle_name: str
    gap_description: str
    headline_hypothesis: str
    test_recommendation: str
    priority_score: Optional[float]
    generated_at: datetime
    model_used: str

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class GenerateBriefRequest(BaseModel):
    theme_id: str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_responses: int
    classified_responses: int
    total_themes: int
    active_themes: int
    total_briefs: int
    top_primary_reasons: list[dict]
    avg_emotional_intensity: Optional[float]
    competitor_mention_pct: Optional[float]
    latest_run: Optional[AnalysisRunOut]
