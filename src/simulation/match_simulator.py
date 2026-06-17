"""
Single-match simulation: given two teams and current strength snapshot,
sample a realistic outcome AND scoreline using our trained models.

Process:
1. Logistic regression -> P(H), P(D), P(A) using current features
2. Sample an outcome from that distribution
3. Poisson model -> home_lambda, away_lambda
4. Sample a scoreline CONSISTENT with the sampled outcome (rejection
   sampling: keep drawing scorelines from the Poisson distributions until
   one matches the sampled outcome — simple, correct, fast enough at our
   scale since most football scorelines align with the favoured outcome
   anyway, so rejection rate is low)
"""

from __future__ import annotations
import numpy as np
from scipy.stats import poisson

import joblib
from pathlib import Path

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

_logreg_bundle = None
_poisson_bundle = None


def _load_models() -> None:
    """Lazy-load models once, reuse across thousands of simulation calls."""
    global _logreg_bundle, _poisson_bundle
    if _logreg_bundle is None:
        _logreg_bundle = joblib.load(MODELS_DIR / "logreg_models.pkl")
    if _poisson_bundle is None:
        _poisson_bundle = joblib.load(MODELS_DIR / "poisson_goals_v2.pkl")


def simulate_match(
    home_team: str,
    away_team: str,
    home_elo: float,
    away_elo: float,
    home_form_points_5: float, away_form_points_5: float,
    home_form_points_10: float, away_form_points_10: float,
    home_form_goals_for_5: float, home_form_goals_against_5: float,
    away_form_goals_for_5: float, away_form_goals_against_5: float,
    home_rest_days: float, away_rest_days: float,
    h2h_home_win_rate: float, h2h_matches_played: int,
    rng: np.random.Generator,
    max_goals: int = 8,
) -> tuple[int, int, str]:
    """
    Returns (home_score, away_score, outcome) for ONE simulated match.
    `rng` is passed in explicitly (not module-level np.random) so results
    are reproducible when we seed it, and independent across parallel runs.
    """
    _load_models()
    logreg_model = _logreg_bundle["uncalibrated"]
    logreg_scaler = _logreg_bundle["scaler"]
    poisson_model = _poisson_bundle["model"]
    poisson_scaler = _poisson_bundle["scaler"]

    elo_diff = home_elo - away_elo

    # --- Step 1: outcome probabilities from logistic regression ---
    X_logreg = np.array([[
        elo_diff, home_elo, away_elo,
        home_form_points_5, away_form_points_5,
        home_form_points_10, away_form_points_10,
        home_form_goals_for_5, home_form_goals_against_5,
        away_form_goals_for_5, away_form_goals_against_5,
        home_rest_days, away_rest_days,
        h2h_home_win_rate, h2h_matches_played,
    ]])
    X_logreg_scaled = logreg_scaler.transform(X_logreg)
    proba = logreg_model.predict_proba(X_logreg_scaled)[0]
    classes = list(logreg_model.classes_)  # e.g. ['A', 'D', 'H']

    # --- Step 2: sample an outcome from that distribution ---
    sampled_outcome = rng.choice(classes, p=proba)

    # --- Step 3: Poisson lambdas for realistic scoreline generation ---
    X_home_poisson = np.array([[
        home_elo, away_elo, elo_diff,
        home_form_points_5, home_form_goals_for_5, home_form_goals_against_5,
        1,  # is_home
    ]])
    X_away_poisson = np.array([[
        away_elo, home_elo, -elo_diff,
        away_form_points_5, away_form_goals_for_5, away_form_goals_against_5,
        0,  # is_home
    ]])
    home_lambda = float(poisson_model.predict(poisson_scaler.transform(X_home_poisson))[0])
    away_lambda = float(poisson_model.predict(poisson_scaler.transform(X_away_poisson))[0])

    # --- Step 4: rejection-sample a scoreline consistent with sampled_outcome ---
    # Most of the time this succeeds in 1-3 tries since lambdas already lean
    # toward the favoured side; cap attempts to avoid any pathological loop.
    for _ in range(200):
        hs = rng.poisson(home_lambda)
        as_ = rng.poisson(away_lambda)
        hs, as_ = min(hs, max_goals), min(as_, max_goals)

        if sampled_outcome == "H" and hs > as_:
            return hs, as_, "H"
        if sampled_outcome == "A" and hs < as_:
            return hs, as_, "A"
        if sampled_outcome == "D" and hs == as_:
            return hs, as_, "D"

    # Fallback (should be extremely rare): force a minimal valid scoreline
    if sampled_outcome == "H":
        return 1, 0, "H"
    if sampled_outcome == "A":
        return 0, 1, "A"
    return 0, 0, "D"


if __name__ == "__main__":
    # Quick manual test: re-use the Austria vs Jordan example from earlier
    rng = np.random.default_rng(seed=42)
    results = []
    for _ in range(10):
        hs, as_, outcome = simulate_match(
            "Austria", "Jordan",
            home_elo=1923.03, away_elo=1759.80,
            home_form_points_5=0.9, away_form_points_5=0.2,
            home_form_points_10=0.8, away_form_points_10=0.3,
            home_form_goals_for_5=2.0, home_form_goals_against_5=0.5,
            away_form_goals_for_5=0.8, away_form_goals_against_5=1.5,
            home_rest_days=14, away_rest_days=14,
            h2h_home_win_rate=0.5, h2h_matches_played=0,
            rng=rng,
        )
        results.append((hs, as_, outcome))
        print(f"Austria {hs} - {as_} Jordan  ({outcome})")

    outcomes = [r[2] for r in results]
    print(f"\nOutcome distribution over 10 sims: "
          f"H={outcomes.count('H')} D={outcomes.count('D')} A={outcomes.count('A')}")