"""
Phase 9b (final): Per-match SHAP explanation, excluding sign-unstable
form features from the display.

WHY FORM FEATURES ARE EXCLUDED FROM DISPLAY: home_form_points_5 (and
related form features) correlate with home_elo_pre at r=0.577. While
form has a clear POSITIVE raw relationship with winning (48.8% -> 72.5%
home win rate across form quartiles, verified directly), the model's
standardized coefficient for form features can occasionally show a
negative sign due to multicollinearity with Elo. Rather than risk
displaying a misleading direction to users, we only surface features
verified to have stable, intuitive SHAP signs: Elo-based features,
head-to-head history, and rest days. The model still USES form features
internally (they contribute measurably to log loss) — we're only
restricting what's shown in the per-match explanation UI, not removing
them from the model.
"""

from __future__ import annotations
import numpy as np
import joblib
import shap
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

# Only features with verified stable SHAP sign direction are shown in the
# per-match explanation UI. Form features are computed and used by the
# model but excluded here — see module docstring.
DISPLAYABLE_FEATURES = {
    "elo_diff": "Overall strength gap (Elo)",
    "home_elo_pre": "Home team's strength rating",
    "away_elo_pre": "Away team's strength rating",
    "home_rest_days": "Home team's rest days",
    "away_rest_days": "Away team's rest days",
    "h2h_home_win_rate": "Head-to-head history",
    "h2h_matches_played": "Number of past meetings",
}

_explainer = None
_model_bundle = None


def _load() -> None:
    global _explainer, _model_bundle
    if _model_bundle is None:
        _model_bundle = joblib.load(MODELS_DIR / "logreg_models.pkl")
    if _explainer is None:
        background = joblib.load(MODELS_DIR / "shap_background.pkl")
        _explainer = shap.LinearExplainer(
            _model_bundle["uncalibrated"], background["explainer_background"]
        )


def explain_match(feature_values: dict[str, float], top_n: int = 5) -> dict:
    _load()
    model = _model_bundle["uncalibrated"]
    scaler = _model_bundle["scaler"]

    X_raw = np.array([[feature_values[col] for col in FEATURE_COLS]])
    X_scaled = scaler.transform(X_raw)

    proba = model.predict_proba(X_scaled)[0]
    classes = list(model.classes_)
    predicted_class = classes[int(np.argmax(proba))]
    predicted_idx = classes.index(predicted_class)

    shap_vals = _explainer.shap_values(X_scaled)
    if isinstance(shap_vals, list):
        shap_for_predicted = shap_vals[predicted_idx][0]
    else:
        shap_for_predicted = shap_vals[0, :, predicted_idx]

    raw_contributions = dict(zip(FEATURE_COLS, shap_for_predicted))

    # Filter to only displayable (sign-stable) features
    display_contributions = {
        DISPLAYABLE_FEATURES[feat]: val
        for feat, val in raw_contributions.items()
        if feat in DISPLAYABLE_FEATURES
    }

    sorted_contributions = sorted(
        display_contributions.items(), key=lambda kv: abs(kv[1]), reverse=True
    )[:top_n]

    outcome_labels = {"H": "Home Win", "D": "Draw", "A": "Away Win"}

    return {
        "probabilities": {
            outcome_labels[c]: round(float(p) * 100, 1)
            for c, p in zip(classes, proba)
        },
        "predicted_outcome": outcome_labels[predicted_class],
        "top_factors": [
            {
                "factor": name,
                "impact": round(float(val) * 100, 1),
                "direction": "increases" if val > 0 else "decreases",
            }
            for name, val in sorted_contributions
        ],
    }


if __name__ == "__main__":
    example = {
        "elo_diff": 163.23, "home_elo_pre": 1923.03, "away_elo_pre": 1759.80,
        "home_form_points_5": 0.9, "away_form_points_5": 0.2,
        "home_form_points_10": 0.8, "away_form_points_10": 0.3,
        "home_form_goals_for_5": 2.0, "home_form_goals_against_5": 0.5,
        "away_form_goals_for_5": 0.8, "away_form_goals_against_5": 1.5,
        "home_rest_days": 14, "away_rest_days": 14,
        "h2h_home_win_rate": 0.5, "h2h_matches_played": 0,
    }

    result = explain_match(example)
    print("=== Austria vs Jordan: explanation (display-filtered) ===")
    print(f"Probabilities: {result['probabilities']}")
    print(f"Predicted outcome: {result['predicted_outcome']}")
    print("\nTop contributing factors:")
    for factor in result["top_factors"]:
        print(f"  {factor['factor']:35s} {factor['direction']:10s} "
              f"by {abs(factor['impact']):.1f} pts")