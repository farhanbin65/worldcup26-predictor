"""
Phase 6: XGBoost outcome model — same chronological split, same features,
direct comparison against the logistic regression baseline (0.8622 log loss).

XGBoost trains gradient-boosted decision trees: each new tree corrects the
errors of the previous ones. Unlike logistic regression, it can capture
nonlinear interactions (e.g. "elo_diff matters less when both teams are
already very strong") without us hand-engineering those interactions.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import log_loss, accuracy_score
from sklearn.preprocessing import LabelEncoder

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


def chronological_split(df: pd.DataFrame, cutoff: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = df[df["date"] < cutoff].copy()
    test = df[df["date"] >= cutoff].copy()
    print(f"[split] train: {len(train):,}  test: {len(test):,}")
    return train, test


def train_xgboost(train: pd.DataFrame, test: pd.DataFrame) -> xgb.XGBClassifier:
    # XGBoost needs integer class labels, not strings ("A","D","H")
    encoder = LabelEncoder()
    y_train = encoder.fit_transform(train["outcome"])
    y_test = encoder.transform(test["outcome"])

    X_train = train[FEATURE_COLS].values
    X_test = test[FEATURE_COLS].values

    model = xgb.XGBClassifier(
        n_estimators=300,       # number of boosting rounds (trees)
        max_depth=4,            # shallow trees prevent overfitting on noisy football data
        learning_rate=0.05,     # small steps per tree, more trees to compensate
        subsample=0.8,          # each tree sees 80% of rows (regularization)
        colsample_bytree=0.8,   # each tree sees 80% of features (regularization)
        objective="multi:softprob",  # outputs calibrated-ish probabilities, not just labels
        eval_metric="mlogloss",
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred_proba = model.predict_proba(X_test)
    y_pred = model.predict(X_test)

    test_ll = log_loss(y_test, y_pred_proba)
    test_acc = accuracy_score(y_test, y_pred)

    print(f"\n[xgboost] Test log loss: {test_ll:.4f}")
    print(f"[xgboost] Test accuracy:  {test_acc:.4f}")
    print(f"[xgboost] Class order:    {list(encoder.classes_)}")

    print("\n=== Feature importance (gain) ===")
    importance = pd.Series(
        model.feature_importances_, index=FEATURE_COLS
    ).sort_values(ascending=False)
    print(importance.round(3))

    return model, encoder


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    train, test = chronological_split(df, TRAIN_CUTOFF)

    model, encoder = train_xgboost(train, test)

    MODELS_DIR.mkdir(exist_ok=True)
    model.save_model(MODELS_DIR / "xgb_outcome.json")
    print(f"\n[saved] -> {MODELS_DIR / 'xgb_outcome.json'}")


if __name__ == "__main__":
    main()