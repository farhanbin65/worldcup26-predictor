"""
Phase 9a: Global SHAP analysis for the logistic regression outcome model.

Since the model is logistic regression (a LINEAR model), SHAP values have
an exact closed-form relationship to the model's coefficients — no
approximation needed (unlike TreeSHAP for ensemble models). We use
shap.LinearExplainer specifically for this reason.

IMPORTANT: SHAP values are computed in the model's STANDARDIZED feature
space (since that's what the model was trained on), but we want to talk
about features in their ORIGINAL units in any explanation. The SHAP
values themselves are still valid and additive regardless of scaling —
only the x-axis interpretation of "feature value" needs the original
units for readability, which shap's plotting handles automatically if
we pass the unscaled data alongside.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import shap

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
TRAIN_CUTOFF = "2023-01-01"

FEATURE_COLS = [
    "elo_diff", "home_elo_pre", "away_elo_pre",
    "home_form_points_5", "away_form_points_5",
    "home_form_points_10", "away_form_points_10",
    "home_form_goals_for_5", "home_form_goals_against_5",
    "away_form_goals_for_5", "away_form_goals_against_5",
    "home_rest_days", "away_rest_days",
    "h2h_home_win_rate", "h2h_matches_played",
]


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    test = df[df["date"] >= TRAIN_CUTOFF].copy()

    bundle = joblib.load(MODELS_DIR / "logreg_models.pkl")
    model = bundle["uncalibrated"]
    scaler = bundle["scaler"]

    X_test_raw = test[FEATURE_COLS].to_numpy(dtype=np.float64)
    X_test_scaled = scaler.transform(X_test_raw)

    print(f"[loaded] model with classes: {model.classes_}")
    print(f"[data] {len(X_test_raw)} test matches for SHAP analysis")

    # LinearExplainer needs a "masker" representing the background
    # distribution (what counts as a "neutral" feature value) — we use
    # the training data's distribution, the standard choice.
    train = df[df["date"] < TRAIN_CUTOFF].copy()
    X_train_scaled = scaler.transform(train[FEATURE_COLS].to_numpy(dtype=np.float64))

    explainer = shap.LinearExplainer(model, X_train_scaled)
    shap_values = explainer.shap_values(X_test_scaled)

    # For multi-class logistic regression, shap_values is shaped
    # (n_samples, n_features, n_classes) in recent shap versions.
    # We focus on the "H" (home win) class for the global summary, since
    # that's the most intuitive single class to interpret first.
    print(f"[shap] raw shap_values shape: {np.array(shap_values).shape}")

    home_idx = list(model.classes_).index("H")
    if isinstance(shap_values, list):
        shap_values_home = shap_values[home_idx]
    else:
        shap_values_home = shap_values[:, :, home_idx]

    # Global importance: mean absolute SHAP value per feature, across all
    # test matches. This answers "which features move predictions the
    # most, on average, regardless of direction?"
    mean_abs_shap = np.abs(shap_values_home).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature": FEATURE_COLS,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False)

    print("\n=== Global feature importance (mean |SHAP value|, Home Win class) ===")
    print(importance_df.to_string(index=False))

    # Save a summary bar plot — this is the one that goes in your README
    MODELS_DIR.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(importance_df["feature"], importance_df["mean_abs_shap"])
    ax.set_xlabel("Mean |SHAP value| (impact on Home Win probability)")
    ax.set_title("Global feature importance — Logistic Regression (SHAP)")
    ax.invert_yaxis()  # highest importance at top
    fig.tight_layout()
    fig_path = MODELS_DIR / "shap_global_importance.png"
    fig.savefig(fig_path, dpi=120, bbox_inches="tight")
    print(f"\n[saved] -> {fig_path}")

    # Save the underlying values too, so the per-match script (next step)
    # and the website don't need to recompute the explainer from scratch
    # every time — though for a single live prediction we WILL recompute,
    # since the explainer is fast and we want fresh SHAP values per request.
    joblib.dump(
        {"explainer_background": X_train_scaled, "feature_cols": FEATURE_COLS},
        MODELS_DIR / "shap_background.pkl",
    )
    print(f"[saved] -> {MODELS_DIR / 'shap_background.pkl'}")


if __name__ == "__main__":
    main()