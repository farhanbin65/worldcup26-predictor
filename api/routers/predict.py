"""
Match prediction endpoint.

Reuses the frozen-feature lookup pattern from tournament_simulator.py and
the SHAP explainer from shap_explain.py — no new modeling logic, just
wiring two already-verified pieces together behind an HTTP endpoint.

IMPORTANT: models are loaded ONCE at module import time (not per request)
since loading joblib/pickle files repeatedly would be slow. This mirrors
the lazy-loading pattern already used in match_simulator.py and
shap_explain.py — we're just triggering that load eagerly at startup here
so the FIRST real request isn't slow.
"""

from __future__ import annotations
from fastapi import APIRouter
from pydantic import BaseModel

from src.simulation.tournament_structure import GROUPS, to_dataset_name
from src.simulation.tournament_simulator import load_frozen_features, load_starting_ratings
from src.models.shap_explain import explain_match

router = APIRouter(prefix="/predict", tags=["predict"])

# Loaded once at import time, reused across all requests
_frozen_features = load_frozen_features()
_current_elo = load_starting_ratings()

# Build a flat list of valid WC2026 team names (current/FIFA names, the
# same ones used throughout GROUPS) for input validation.
_valid_teams = sorted({team for group in GROUPS.values() for team in group})


class PredictionRequest(BaseModel):
    home_team: str
    away_team: str


@router.get("/teams")
def list_valid_teams():
    """Returns the list of valid WC2026 team names for prediction requests."""
    return {"teams": _valid_teams}


@router.post("/match")
def predict_match(request: PredictionRequest):
    """
    Predicts the outcome of a hypothetical match between two WC2026 teams,
    using current Elo + frozen form/h2h features, with a SHAP explanation.
    """
    home_team = request.home_team
    away_team = request.away_team

    if home_team not in _valid_teams:
        return {"error": f"'{home_team}' is not a valid WC2026 team. See /predict/teams for the full list."}
    if away_team not in _valid_teams:
        return {"error": f"'{away_team}' is not a valid WC2026 team. See /predict/teams for the full list."}
    if home_team == away_team:
        return {"error": "home_team and away_team must be different."}

    home_ds = to_dataset_name(home_team)
    away_ds = to_dataset_name(away_team)

    feat_home = _frozen_features[home_ds]
    feat_away = _frozen_features[away_ds]

    home_elo = _current_elo.get(home_ds, 1500.0)
    away_elo = _current_elo.get(away_ds, 1500.0)

    feature_values = {
        "elo_diff": home_elo - away_elo,
        "home_elo_pre": home_elo, "away_elo_pre": away_elo,
        "home_form_points_5": feat_home["form_points_5"],
        "away_form_points_5": feat_away["form_points_5"],
        "home_form_points_10": feat_home["form_points_10"],
        "away_form_points_10": feat_away["form_points_10"],
        "home_form_goals_for_5": feat_home["form_goals_for_5"],
        "home_form_goals_against_5": feat_home["form_goals_against_5"],
        "away_form_goals_for_5": feat_away["form_goals_for_5"],
        "away_form_goals_against_5": feat_away["form_goals_against_5"],
        "home_rest_days": 4, "away_rest_days": 4,  # typical WC group-stage spacing
        "h2h_home_win_rate": 0.5, "h2h_matches_played": 0,  # simplified, same as simulator
    }

    result = explain_match(feature_values)

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_elo": round(home_elo, 1),
        "away_elo": round(away_elo, 1),
        **result,
    }