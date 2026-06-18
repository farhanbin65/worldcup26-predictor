"""
Phase 7: Calibration check for the logistic regression outcome model.

We check: when the model says "P(home win) = 0.70", does the home team
actually win ~70% of the time across all matches where it said that?

If miscalibrated, we apply a fix (isotonic regression or Platt scaling)
BEFORE these probabilities feed into the Monte Carlo simulator in Phase 8 —
miscalibration compounds across simulated tournament rounds.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import calibration_curve, CalibratedClassifierCV
from sklearn.metrics import log_loss, brier_score_loss

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
    train = df[df["date"] < TRAIN_CUTOFF].copy()
    test = df[df["date"] >= TRAIN_CUTOFF].copy()

    # .to_numpy() forces a real numpy array, unlike .values which can leave
    # pyarrow-backed dtypes intact when the source DataFrame was read from
    # parquet. CalibratedClassifierCV's internal CV indexing breaks on those.
    X_train = train[FEATURE_COLS].to_numpy(dtype=np.float64)
    y_train = train["outcome"].to_numpy()
    X_test = test[FEATURE_COLS].to_numpy(dtype=np.float64)
    y_test = test["outcome"].to_numpy()

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    base_model = LogisticRegression(max_iter=1000, random_state=42)
    base_model.fit(X_train_scaled, y_train)

    proba_uncalibrated = base_model.predict_proba(X_test_scaled)
    home_idx = list(base_model.classes_).index("H")
    home_win_proba = proba_uncalibrated[:, home_idx]
    y_test_home_binary = (y_test == "H").astype(int)

    # --- Reliability check: bucket predictions, compare to actual frequency ---
    print("=== Calibration check: UNCALIBRATED logistic regression ===")
    fraction_pos, mean_predicted = calibration_curve(
        y_test_home_binary, home_win_proba, n_bins=10, strategy="quantile"
    )
    print(f"{'Predicted prob':>16} | {'Actual frequency':>16} | {'Gap':>8}")
    for pred, actual in zip(mean_predicted, fraction_pos):
        gap = actual - pred
        flag = "  <-- overconfident" if gap < -0.03 else ("  <-- underconfident" if gap > 0.03 else "")
        print(f"{pred:16.3f} | {actual:16.3f} | {gap:+8.3f}{flag}")

    brier_uncal = brier_score_loss(y_test_home_binary, home_win_proba)
    print(f"\nBrier score (home win, uncalibrated): {brier_uncal:.4f}")

    # --- Apply isotonic calibration via cross-validation on TRAINING data only ---
    # CalibratedClassifierCV refits using internal CV folds on the train set,
    # so the test set remains untouched until final evaluation — same
    # discipline as the chronological split itself.
    calibrated_model = CalibratedClassifierCV(
        LogisticRegression(max_iter=1000, random_state=42),
        method="sigmoid",  # Platt scaling — fits a single sigmoid, far less
                            # prone to overfitting than isotonic on ~46k rows
        cv=5,
    )
    calibrated_model.fit(X_train_scaled, y_train)

    proba_calibrated = calibrated_model.predict_proba(X_test_scaled)
    home_idx_cal = list(calibrated_model.classes_).index("H")
    home_win_proba_cal = proba_calibrated[:, home_idx_cal]

    print("\n=== Calibration check: CALIBRATED (Platt/sigmoid) logistic regression ===")
    fraction_pos_cal, mean_predicted_cal = calibration_curve(
        y_test_home_binary, home_win_proba_cal, n_bins=10, strategy="quantile"
    )
    print(f"{'Predicted prob':>16} | {'Actual frequency':>16} | {'Gap':>8}")
    for pred, actual in zip(mean_predicted_cal, fraction_pos_cal):
        gap = actual - pred
        flag = "  <-- overconfident" if gap < -0.03 else ("  <-- underconfident" if gap > 0.03 else "")
        print(f"{pred:16.3f} | {actual:16.3f} | {gap:+8.3f}{flag}")

    brier_cal = brier_score_loss(y_test_home_binary, home_win_proba_cal)
    ll_uncal = log_loss(y_test, proba_uncalibrated, labels=base_model.classes_)
    ll_cal = log_loss(y_test, proba_calibrated, labels=calibrated_model.classes_)

    print(f"\nBrier score (home win, calibrated):   {brier_cal:.4f}")
    print(f"\nFull 3-class log loss, uncalibrated: {ll_uncal:.4f}")
    print(f"Full 3-class log loss, calibrated:   {ll_cal:.4f}")

    # --- Plot reliability diagram for visual confirmation ---
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    ax.plot(mean_predicted, fraction_pos, "o-", label="Uncalibrated")
    ax.plot(mean_predicted_cal, fraction_pos_cal, "s-", label="Calibrated (isotonic)")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Actual fraction of home wins")
    ax.set_title("Calibration curve: Home Win prediction")
    ax.legend()
    ax.grid(alpha=0.3)

    MODELS_DIR.mkdir(exist_ok=True)
    fig_path = MODELS_DIR / "calibration_curve.png"
    fig.savefig(fig_path, dpi=120, bbox_inches="tight")
    print(f"\n[saved plot] -> {fig_path}")

    # Save whichever model wins (decide after seeing the numbers)
    import joblib
    joblib.dump(
        {"uncalibrated": base_model, "calibrated": calibrated_model, "scaler": scaler},
        MODELS_DIR / "logreg_models.pkl",
    )
    print(f"[saved] -> {MODELS_DIR / 'logreg_models.pkl'}")


if __name__ == "__main__":
    main()