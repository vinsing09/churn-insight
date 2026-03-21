import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account, analysis, auth, briefs, dashboard, integrations, themes
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data/embeddings", exist_ok=True)
    yield


app = FastAPI(title="Churn Insight API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
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


@app.get("/")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
