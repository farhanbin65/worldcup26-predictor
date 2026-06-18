"""
Phase 6b: Hyperparameter tuning for XGBoost — done correctly.

Critical rule: tune using a validation slice carved from TRAINING data only.
The final test set (2023-2026) is touched exactly ONCE, at the end, with the
winning config. Repeatedly checking the test set during tuning would be
"evaluation leakage" — silently overfitting our hyperparameter choices to
data we're supposed to be holding out.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd
import xgboost as xgb
from sklearn.metrics import log_loss
from sklearn.preprocessing import LabelEncoder

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")

TRAIN_CUTOFF = "2023-01-01"   # final test set starts here (untouched until the end)
VAL_CUTOFF = "2021-01-01"     # validation slice: 2021-01-01 to 2023-01-01

FEATURE_COLS = [
    "elo_diff", "home_elo_pre", "away_elo_pre",
    "home_form_points_5", "away_form_points_5",
    "home_form_points_10", "away_form_points_10",
    "home_form_goals_for_5", "home_form_goals_against_5",
    "away_form_goals_for_5", "away_form_goals_against_5",
    "home_rest_days", "away_rest_days",
    "h2h_home_win_rate", "h2h_matches_played",
]

# A small, sane grid — not exhaustive, just enough to see if there's a clear winner
CONFIGS = [
    {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.1},
    {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.05},
    {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05},  # our original
    {"n_estimators": 500, "max_depth": 3, "learning_rate": 0.03},
    {"n_estimators": 150, "max_depth": 2, "learning_rate": 0.1},
    {"n_estimators": 400, "max_depth": 5, "learning_rate": 0.02},
]


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")

    # Three-way split: train_tune (fit) -> val (pick config) -> test (final, untouched)
    train_tune = df[df["date"] < VAL_CUTOFF].copy()
    val = df[(df["date"] >= VAL_CUTOFF) & (df["date"] < TRAIN_CUTOFF)].copy()
    test = df[df["date"] >= TRAIN_CUTOFF].copy()

    print(f"[split] train_tune: {len(train_tune):,}  val: {len(val):,}  test: {len(test):,}")

    encoder = LabelEncoder()
    y_tune = encoder.fit_transform(train_tune["outcome"])
    y_val = encoder.transform(val["outcome"])
    y_test = encoder.transform(test["outcome"])

    X_tune = train_tune[FEATURE_COLS].values
    X_val = val[FEATURE_COLS].values
    X_test = test[FEATURE_COLS].values

    print("\n=== Tuning on validation slice (test set NOT touched yet) ===")
    results = []
    for cfg in CONFIGS:
        model = xgb.XGBClassifier(
            **cfg,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42,
        )
        model.fit(X_tune, y_tune)
        val_proba = model.predict_proba(X_val)
        val_ll = log_loss(y_val, val_proba)
        results.append((cfg, val_ll))
        print(f"  {cfg}  ->  val log loss: {val_ll:.4f}")

    best_cfg, best_val_ll = min(results, key=lambda r: r[1])
    print(f"\n[winner] {best_cfg} (val log loss {best_val_ll:.4f})")

    # Refit the winning config on ALL pre-test data (train_tune + val combined),
    # then evaluate ONCE on the held-out test set for the final honest number.
    print("\n=== Final evaluation on untouched test set (2023-2026) ===")
    final_train = df[df["date"] < TRAIN_CUTOFF].copy()
    y_final_train = encoder.transform(final_train["outcome"])
    X_final_train = final_train[FEATURE_COLS].values

    final_model = xgb.XGBClassifier(
        **best_cfg,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )
    final_model.fit(X_final_train, y_final_train)
    test_proba = final_model.predict_proba(X_test)
    test_ll = log_loss(y_test, test_proba)
    print(f"[final xgboost, tuned] Test log loss: {test_ll:.4f}")
    print(f"(compare: logistic regression was 0.8622, untuned xgboost was 0.8640)")

    MODELS_DIR.mkdir(exist_ok=True)
    final_model.save_model(MODELS_DIR / "xgb_outcome_tuned.json")
    print(f"\n[saved] -> {MODELS_DIR / 'xgb_outcome_tuned.json'}")


if __name__ == "__main__":
    main()