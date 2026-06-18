"""
Phase 5: Baseline logistic regression model for match outcome prediction.

Chronological train/test split — NEVER random — because we need the test
set to simulate "predicting the future using only the past", exactly the
real deployment scenario for WC2026.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, accuracy_score, brier_score_loss
from sklearn.preprocessing import StandardScaler

PROCESSED_DIR = Path("data/processed")
TRAIN_CUTOFF = "2023-01-01"  # train: everything before this date
                              # test:  everything from this date onward

FEATURE_COLS = [
    "elo_diff", "home_elo_pre", "away_elo_pre",
    "home_form_points_5", "away_form_points_5",
    "home_form_points_10", "away_form_points_10",
    "home_form_goals_for_5", "home_form_goals_against_5",
    "away_form_goals_for_5", "away_form_goals_against_5",
    "home_rest_days", "away_rest_days",
    "h2h_home_win_rate", "h2h_matches_played",
]


def chronological_split(df: pd.DataFrame, cutoff: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by date, not by row index or random sampling — see module docstring."""
    train = df[df["date"] < cutoff].copy()
    test = df[df["date"] >= cutoff].copy()
    print(f"[split] train: {len(train):,} matches ({train['date'].min().date()} -> {train['date'].max().date()})")
    print(f"[split] test:  {len(test):,} matches ({test['date'].min().date()} -> {test['date'].max().date()})")
    return train, test


def naive_baselines(test: pd.DataFrame) -> None:
    """
    Two "dumb" reference points our model MUST beat, or it's worthless:
      1. Random guessing: 1/3 probability to each class.
      2. Elo-only: the home_win_prob_elo we already computed for free.
    """
    n = len(test)
    y_true = test["outcome"].values

    # Random: uniform 1/3, 1/3, 1/3 for every match
    random_probs = np.full((n, 3), 1 / 3)
    classes = ["A", "D", "H"]  # alphabetical, matches sklearn's default ordering
    y_true_idx = test["outcome"].map({"A": 0, "D": 1, "H": 2}).values
    random_ll = log_loss(y_true_idx, random_probs, labels=[0, 1, 2])
    print(f"\n[baseline] Random guess log loss:        {random_ll:.4f}")

    # Elo-only: convert home_win_prob_elo into a crude 3-class split
    # (we don't have a draw model yet, so this is deliberately rough)
    elo_home = test["home_win_prob_elo"].values
    elo_draw = np.full(n, 0.25)  # crude flat draw estimate
    elo_away = 1 - elo_home - elo_draw
    elo_away = np.clip(elo_away, 0.01, 0.98)
    elo_probs = np.column_stack([elo_away, elo_draw, elo_home])
    elo_probs = elo_probs / elo_probs.sum(axis=1, keepdims=True)  # renormalize
    elo_ll = log_loss(y_true_idx, elo_probs, labels=[0, 1, 2])
    print(f"[baseline] Elo-only (crude) log loss:     {elo_ll:.4f}")


def train_logistic_regression(train: pd.DataFrame, test: pd.DataFrame) -> None:
    X_train = train[FEATURE_COLS].values
    y_train = train["outcome"].values
    X_test = test[FEATURE_COLS].values
    y_test = test["outcome"].values

    # Scale features: logistic regression's optimizer converges faster and
    # more reliably when features are on similar scales (Elo ~1500-2200,
    # rest_days ~0-180, h2h_win_rate ~0-1 — wildly different ranges otherwise).
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # fit on train ONLY, transform test

    model = LogisticRegression(
        max_iter=1000,
        random_state=42,
    )
    model.fit(X_train_scaled, y_train)

    y_pred_proba = model.predict_proba(X_test_scaled)
    y_pred = model.predict(X_test_scaled)

    test_ll = log_loss(y_test, y_pred_proba, labels=model.classes_)
    test_acc = accuracy_score(y_test, y_pred)

    print(f"\n[logistic regression] Test log loss: {test_ll:.4f}")
    print(f"[logistic regression] Test accuracy:  {test_acc:.4f}")
    print(f"[logistic regression] Class order:    {model.classes_}")

    print("\n=== Coefficients (per class, standardized features) ===")
    coef_df = pd.DataFrame(model.coef_, columns=FEATURE_COLS, index=model.classes_)
    print(coef_df.round(3).T)


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    train, test = chronological_split(df, TRAIN_CUTOFF)

    naive_baselines(test)
    train_logistic_regression(train, test)


if __name__ == "__main__":
    main()