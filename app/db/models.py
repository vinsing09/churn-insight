from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    plan: Mapped[str] = mapped_column(String, default="trial")
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ad_copy: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    integrations: Mapped[list["Integration"]] = relationship(back_populates="account")
    responses: Mapped[list["Response"]] = relationship(back_populates="account")
    themes: Mapped[list["Theme"]] = relationship(back_populates="account")
    briefs: Mapped[list["Brief"]] = relationship(back_populates="account")
    analysis_runs: Mapped[list["AnalysisRun"]] = relationship(back_populates="account")


class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account: Mapped["Account"] = relationship(back_populates="integrations")


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (UniqueConstraint("account_id", "source", "source_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    text_stripped: Mapped[str] = mapped_column(Text, nullable=False)
    text_raw_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    account: Mapped["Account"] = relationship(back_populates="responses")
    classification: Mapped[Optional["Classification"]] = relationship(back_populates="response")
    theme_responses: Mapped[list["ThemeResponse"]] = relationship(back_populates="response")


class Classification(Base):
    __tablename__ = "classifications"

    response_id: Mapped[str] = mapped_column(String, ForeignKey("responses.id"), primary_key=True)
    primary_reason: Mapped[str] = mapped_column(String, nullable=False)
    competitor_mentioned: Mapped[bool] = mapped_column(Boolean, default=False)
    competitor_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    emotional_intensity: Mapped[int] = mapped_column(Integer, nullable=False)
    marketing_actionability: Mapped[str] = mapped_column(String, nullable=False)
    key_phrases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    classified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_used: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    response: Mapped["Response"] = relationship(back_populates="classification")


class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_emotional_intensity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competitor_mention_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="active")

    account: Mapped["Account"] = relationship(back_populates="themes")
    theme_responses: Mapped[list["ThemeResponse"]] = relationship(back_populates="theme")
    briefs: Mapped[list["Brief"]] = relationship(back_populates="theme")


class ThemeResponse(Base):
    __tablename__ = "theme_responses"
    __table_args__ = (PrimaryKeyConstraint("theme_id", "response_id"),)

    theme_id: Mapped[str] = mapped_column(String, ForeignKey("themes.id"), nullable=False)
    response_id: Mapped[str] = mapped_column(String, ForeignKey("responses.id"), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)

    theme: Mapped["Theme"] = relationship(back_populates="theme_responses")
    response: Mapped["Response"] = relationship(back_populates="theme_responses")


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    theme_id: Mapped[str] = mapped_column(String, ForeignKey("themes.id"), nullable=False)
    angle_name: Mapped[str] = mapped_column(String, nullable=False)
    gap_description: Mapped[str] = mapped_column(Text, nullable=False)
    headline_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    test_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_used: Mapped[str] = mapped_column(String, nullable=False)

    account: Mapped["Account"] = relationship(back_populates="briefs")
    theme: Mapped["Theme"] = relationship(back_populates="briefs")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("accounts.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    responses_processed: Mapped[int] = mapped_column(Integer, default=0)
    new_responses: Mapped[int] = mapped_column(Integer, default=0)
    themes_detected: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    account: Mapped["Account"] = relationship(back_populates="analysis_runs")
