"""
admin.py — protected admin endpoints.
POST /admin/sync triggers sync.py to pull latest results and optionally
re-run Monte Carlo.

Protect with a secret header: X-Sync-Secret
Set SYNC_SECRET in your environment (Render dashboard → Environment).
"""

import os
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/admin", tags=["admin"])

SYNC_SECRET = os.getenv("SYNC_SECRET", "")
SYNC_SCRIPT = Path(__file__).parent.parent.parent / "src" / "simulation" / "sync.py"


@router.post("/sync")
async def sync_results(
    run_sim: bool = True,
    x_sync_secret: str = Header(default=""),
):
    if not SYNC_SECRET:
        raise HTTPException(status_code=500, detail="SYNC_SECRET not configured on server")
    if x_sync_secret != SYNC_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    cmd = [sys.executable, str(SYNC_SCRIPT), "--write"]
    if run_sim:
        cmd.append("--run-sim")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=SYNC_SCRIPT.parent.parent.parent)

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Sync failed:\n{result.stderr}")

    return {
        "status": "ok",
        "output": result.stdout,
    }