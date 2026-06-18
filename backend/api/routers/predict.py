"""
Match prediction endpoint — SHAP-free version for production deployment.

WHY NO SHAP HERE: shap's import alone costs ~175MB RSS (largely from its
numba dependency), pushing total API memory past what Render's free tier
comfortably supports. SHAP explanations are still generated and validated
offline (see src/models/shap_explain.py, src/models/shap_global.py) and
documented in the project README/report. This endpoint instead surfaces
the model's directly interpretable elements: probabilities and the
strongest contributing signal (elo_diff), which we've independently
verified (Phase 5, 6, 9) is the dominant feature by a wide margin in
every analysis method tried.
"""

from __future__ import annotations
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
import joblib
from pathlib import Path

from src.simulation.tournament_structure import GROUPS, to_dataset_name
from src.simulation.tournament_simulator import load_frozen_features, load_starting_ratings

router = APIRouter(prefix="/predict", tags=["predict"])

MODELS_DIR = Path("models")

FEATURE_COLS = [
    "elo_diff", "home_elo_pre", "away_elo_pre",
    "home_form_points_5", "away_form_points_5",
    "home_form_points_10", "away_form_points_10",
    "home_form_goals_for_5", "home_form_goals_against_5",
    "away_form_goals_for_5", "away_form_goals_against_5",
    "home_rest_days", "away_rest_days",
    "h2h_home_win_rate", "h2h_matches_played",
]

_model_bundle = joblib.load(MODELS_DIR / "logreg_models.pkl")
_frozen_features = load_frozen_features()
_current_elo = load_starting_ratings()
_valid_teams = sorted({team for group in GROUPS.values() for team in group})


class PredictionRequest(BaseModel):
    home_team: str
    away_team: str


@router.get("/teams")
def list_valid_teams():
    return {"teams": _valid_teams}


@router.post("/match")
def predict_match(request: PredictionRequest):
    home_team, away_team = request.home_team, request.away_team

    if home_team not in _valid_teams:
        return {"error": f"'{home_team}' is not a valid WC2026 team. See /predict/teams."}
    if away_team not in _valid_teams:
        return {"error": f"'{away_team}' is not a valid WC2026 team. See /predict/teams."}
    if home_team == away_team:
        return {"error": "home_team and away_team must be different."}

    home_ds, away_ds = to_dataset_name(home_team), to_dataset_name(away_team)
    feat_home, feat_away = _frozen_features[home_ds], _frozen_features[away_ds]
    home_elo = _current_elo.get(home_ds, 1500.0)
    away_elo = _current_elo.get(away_ds, 1500.0)

    model, scaler = _model_bundle["uncalibrated"], _model_bundle["scaler"]

    X = np.array([[
        home_elo - away_elo, home_elo, away_elo,
        feat_home["form_points_5"], feat_away["form_points_5"],
        feat_home["form_points_10"], feat_away["form_points_10"],
        feat_home["form_goals_for_5"], feat_home["form_goals_against_5"],
        feat_away["form_goals_for_5"], feat_away["form_goals_against_5"],
        4, 4, 0.5, 0,
    ]])
    proba = model.predict_proba(scaler.transform(X))[0]
    classes = list(model.classes_)
    outcome_labels = {"H": "Home Win", "D": "Draw", "A": "Away Win"}

    elo_gap = home_elo - away_elo
    favoured = home_team if elo_gap > 0 else away_team
    summary = (
        f"{favoured} is favoured based primarily on overall strength rating "
        f"(Elo gap: {abs(elo_gap):.0f} points), the model's most influential factor."
    )

    return {
        "home_team": home_team, "away_team": away_team,
        "home_elo": round(home_elo, 1), "away_elo": round(away_elo, 1),
        "probabilities": {
            outcome_labels[c]: round(float(p) * 100, 1) for c, p in zip(classes, proba)
        },
        "predicted_outcome": outcome_labels[classes[int(np.argmax(proba))]],
        "summary": summary,
    }