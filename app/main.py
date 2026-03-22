import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account, analysis, auth, briefs, dashboard, integrations, themes
from app.api.account import admin_router
from app.core.config import settings

app = FastAPI(title="Churn Insight API", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    if os.getenv("SCHEDULER_ENABLED", "false").lower() == "true":
        try:
            from app.services.scheduler import start_scheduler
            start_scheduler()
            print("Scheduler started", flush=True)
        except Exception as e:
            print(f"Scheduler failed to start: {e}", flush=True)

    Path("data/embeddings").mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_origin_regex=r"https://.*\.lovable\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(integrations.router, prefix=PREFIX)
app.include_router(analysis.router, prefix=PREFIX)
app.include_router(themes.router, prefix=PREFIX)
app.include_router(briefs.router, prefix=PREFIX)
app.include_router(dashboard.router, prefix=PREFIX)
app.include_router(account.router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)


@app.get("/")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
