"""
FastAPI application entrypoint.

Architecture note: this app loads trained models ONCE at startup (not per
request) since loading a pickle/joblib file on every API call would be
slow and wasteful. FastAPI's lifespan/startup event handles this.
"""

from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="World Cup 2026 Predictor API",
    description="ML-powered match predictions, group standings, and tournament simulation for WC2026",
    version="0.1.0",
)

# CORS: allow the Next.js frontend (different origin in dev AND prod) to
# call this API. Wide open for now during development; tighten to the
# specific deployed frontend URL before considering this production-ready.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict to actual frontend domain before final deploy
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "WC2026 Predictor API is running"}


@app.get("/health")
def health_check():
    """Simple endpoint to verify the API is alive — useful for Render's health checks."""
    return {"status": "healthy"}