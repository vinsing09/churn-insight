"""Verify the full data flow via the REST API.

Requires uvicorn running: uvicorn app.main:app --port 8090

Usage:
    python scripts/verify_api.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from rich.console import Console
from rich.syntax import Syntax

BASE = "http://localhost:8090/api/v1"
EMAIL = "vineet.singh1208@gmail.com"
PASSWORD = "testpassword123"  # change if you registered with a different password
console = Console()


def _pp(data) -> None:
    console.print(Syntax(json.dumps(data, indent=2, default=str), "json", theme="monokai"))


def main() -> None:
    client = httpx.Client(base_url=BASE, timeout=10)

    # ── Login ─────────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]POST /auth/login[/bold cyan]")
    resp = client.post("/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if resp.status_code != 200:
        console.print(f"[red]Login failed ({resp.status_code}):[/red] {resp.text}")
        console.print("Make sure you registered with the same password this script uses.")
        sys.exit(1)
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    console.print("[green]✓ Logged in[/green]")

    # ── Dashboard summary ─────────────────────────────────────────────────────
    console.print("\n[bold cyan]GET /dashboard/summary[/bold cyan]")
    resp = client.get("/dashboard/summary", headers=headers)
    resp.raise_for_status()
    _pp(resp.json())

    # ── Themes ────────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]GET /themes[/bold cyan]")
    resp = client.get("/themes", headers=headers)
    resp.raise_for_status()
    themes = resp.json()
    _pp(themes)

    # ── Briefs ────────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]GET /briefs[/bold cyan]")
    resp = client.get("/briefs", headers=headers)
    resp.raise_for_status()
    _pp(resp.json())

    console.print(f"\n[bold green]✓ API verification complete.[/bold green]")
    console.print(f"  Themes: {len(themes)}")


if __name__ == "__main__":
    main()
