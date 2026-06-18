"""
Poisson goals model, v2 — dropped one-hot team identity entirely.

WHY THE FIRST VERSION FAILED: one-hot team/opponent encoding (666 columns)
and elo_diff (1 column) both encode "team strength", just at different
granularities. Under L2 regularization, the high-cardinality one-hot
features absorbed all the signal and elo_diff/is_home were zeroed out
completely (verified: both coefficients were exactly 0.0).

FIX: use the same strength signals as the working logistic regression
model (elo, recent form) instead of raw team identity. This also makes
the model usable for ANY team pairing, including teams with few
historical matches, since it doesn't need to have "seen" that exact team
sLOTS of times to learn a meaningful one-hot weight.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_poisson_deviance
import joblib

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("models")
TRAIN_CUTOFF = "2023-01-01"
MAX_GOALS = 8

# Continuous strength features only — no team one-hot encoding.
# This mirrors what already worked for the logistic regression model.
STRENGTH_FEATURES = [
    "team_elo", "opp_elo", "elo_diff_signed",
    "team_form_points_5", "team_form_goals_for_5", "team_form_goals_against_5",
    "is_home",
]


def build_team_strength_features(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (team, match) appearance, using only continuous strength signals."""
    home_rows = pd.DataFrame({
        "goals_for": df["home_score"],
        "team_elo": df["home_elo_pre"], "opp_elo": df["away_elo_pre"],
        "elo_diff_signed": df["elo_diff"],
        "team_form_points_5": df["home_form_points_5"],
        "team_form_goals_for_5": df["home_form_goals_for_5"],
        "team_form_goals_against_5": df["home_form_goals_against_5"],
        "is_home": 1,
    })
    away_rows = pd.DataFrame({
        "goals_for": df["away_score"],
        "team_elo": df["away_elo_pre"], "opp_elo": df["home_elo_pre"],
        "elo_diff_signed": -df["elo_diff"],
        "team_form_points_5": df["away_form_points_5"],
        "team_form_goals_for_5": df["away_form_goals_for_5"],
        "team_form_goals_against_5": df["away_form_goals_against_5"],
        "is_home": 0,
    })
    return pd.concat([home_rows, away_rows], ignore_index=True)


def train_poisson(train_long: pd.DataFrame) -> tuple[PoissonRegressor, StandardScaler]:
    X_raw = train_long[STRENGTH_FEATURES].values
    y = train_long["goals_for"].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    # Lower alpha now that we have only 7 features competing fairly —
    # no high-cardinality categorical to absorb everything.
    model = PoissonRegressor(alpha=0.1, max_iter=1000)
    model.fit(X, y)
    return model, scaler


def predict_lambda(model, scaler, team_elo, opp_elo, elo_diff_signed,
                    form_points_5, form_gf_5, form_ga_5, is_home) -> float:
    row = np.array([[team_elo, opp_elo, elo_diff_signed,
                      form_points_5, form_gf_5, form_ga_5, is_home]])
    row_scaled = scaler.transform(row)
    return float(model.predict(row_scaled)[0])


def scoreline_matrix(home_lambda: float, away_lambda: float, max_goals: int = MAX_GOALS) -> np.ndarray:
    home_probs = poisson.pmf(np.arange(max_goals + 1), home_lambda)
    away_probs = poisson.pmf(np.arange(max_goals + 1), away_lambda)
    return np.outer(home_probs, away_probs)


def outcome_probs_from_matrix(matrix: np.ndarray) -> dict[str, float]:
    """
    Sum the scoreline matrix into H/D/A probabilities, then renormalize.
    Renormalization is needed because MAX_GOALS truncates the Poisson's
    infinite support — the 9x9 grid captures slightly less than 100% of
    probability mass, so raw sums won't add to exactly 1.0. We rescale so
    they do, which is the standard fix (the missing tail mass is negligible
    for realistic football lambdas, typically <0.1%).
    """
    home_win = np.tril(matrix, k=-1).sum()
    draw = np.trace(matrix)
    away_win = np.triu(matrix, k=1).sum()
    total = home_win + draw + away_win
    return {"H": home_win / total, "D": draw / total, "A": away_win / total}


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    train = df[df["date"] < TRAIN_CUTOFF].copy()
    test = df[df["date"] >= TRAIN_CUTOFF].copy()
    print(f"[split] train: {len(train):,}  test: {len(test):,}")

    train_long = build_team_strength_features(train)
    model, scaler = train_poisson(train_long)

    print("\n=== Coefficients (standardized features) ===")
    for name, coef in zip(STRENGTH_FEATURES, model.coef_):
        print(f"  {name:30s} {coef:+.4f}")

    # Sanity check: same matchup as before, now with continuous features
    print("\n=== Sanity check: example matchup ===")
    test_row = test.iloc[-1]
    h_team, a_team = test_row["home_team"], test_row["away_team"]

    home_lambda = predict_lambda(
        model, scaler,
        team_elo=test_row["home_elo_pre"], opp_elo=test_row["away_elo_pre"],
        elo_diff_signed=test_row["elo_diff"],
        form_points_5=test_row["home_form_points_5"],
        form_gf_5=test_row["home_form_goals_for_5"],
        form_ga_5=test_row["home_form_goals_against_5"],
        is_home=1,
    )
    away_lambda = predict_lambda(
        model, scaler,
        team_elo=test_row["away_elo_pre"], opp_elo=test_row["home_elo_pre"],
        elo_diff_signed=-test_row["elo_diff"],
        form_points_5=test_row["away_form_points_5"],
        form_gf_5=test_row["away_form_goals_for_5"],
        form_ga_5=test_row["away_form_goals_against_5"],
        is_home=0,
    )
    print(f"{h_team} (home) expected goals: {home_lambda:.2f}")
    print(f"{a_team} (away) expected goals: {away_lambda:.2f}")
    print(f"Actual result: {test_row['home_score']}-{test_row['away_score']}")

    matrix = scoreline_matrix(home_lambda, away_lambda)
    outcome_probs = outcome_probs_from_matrix(matrix)
    print(f"\nDerived outcome probs: H={outcome_probs['H']:.3f}  "
          f"D={outcome_probs['D']:.3f}  A={outcome_probs['A']:.3f}")

    most_likely_idx = np.unravel_index(matrix.argmax(), matrix.shape)
    print(f"Most likely scoreline: {most_likely_idx[0]}-{most_likely_idx[1]} "
          f"(p={matrix[most_likely_idx]:.3f})")
    # Quantitative evaluation across the WHOLE test set, not just one example
    print("\n=== Full test set evaluation ===")
    test_long_home = build_team_strength_features(test)
    # we only need the "home perspective" half for a clean per-match deviance check
    n_test = len(test)

    home_lambdas, away_lambdas = [], []
    for row in test.itertuples(index=False):
        hl = predict_lambda(
            model, scaler, row.home_elo_pre, row.away_elo_pre, row.elo_diff,
            row.home_form_points_5, row.home_form_goals_for_5,
            row.home_form_goals_against_5, is_home=1,
        )
        al = predict_lambda(
            model, scaler, row.away_elo_pre, row.home_elo_pre, -row.elo_diff,
            row.away_form_points_5, row.away_form_goals_for_5,
            row.away_form_goals_against_5, is_home=0,
        )
        home_lambdas.append(hl)
        away_lambdas.append(al)

    home_lambdas = np.array(home_lambdas)
    away_lambdas = np.array(away_lambdas)

    home_deviance = mean_poisson_deviance(test["home_score"].values, home_lambdas)
    away_deviance = mean_poisson_deviance(test["away_score"].values, away_lambdas)
    print(f"Mean Poisson deviance (home goals): {home_deviance:.4f}")
    print(f"Mean Poisson deviance (away goals): {away_deviance:.4f}")
    print("(lower is better; compare against a 'predict the mean' baseline below)")

    # Naive baseline: always predict the training set's average goals scored
    naive_home_pred = np.full(n_test, train["home_score"].mean())
    naive_away_pred = np.full(n_test, train["away_score"].mean())
    naive_home_dev = mean_poisson_deviance(test["home_score"].values, naive_home_pred)
    naive_away_dev = mean_poisson_deviance(test["away_score"].values, naive_away_pred)
    print(f"\nNaive baseline deviance (home): {naive_home_dev:.4f}")
    print(f"Naive baseline deviance (away): {naive_away_dev:.4f}")

    # Derive outcome accuracy from the Poisson model across the whole test set,
    # to cross-check against logistic regression's 0.8622 log loss
    from sklearn.metrics import log_loss
    outcome_probs_list = []
    for hl, al in zip(home_lambdas, away_lambdas):
        probs = outcome_probs_from_matrix(scoreline_matrix(hl, al))
        outcome_probs_list.append([probs["A"], probs["D"], probs["H"]])  # alphabetical order
    outcome_probs_arr = np.array(outcome_probs_list)
    y_true_idx = test["outcome"].map({"A": 0, "D": 1, "H": 2}).values
    poisson_derived_ll = log_loss(y_true_idx, outcome_probs_arr, labels=[0, 1, 2])
    print(f"\n[cross-check] Outcome log loss DERIVED from Poisson scorelines: {poisson_derived_ll:.4f}")
    print("(compare: logistic regression direct = 0.8622, XGBoost tuned = 0.8635)")

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"model": model, "scaler": scaler}, MODELS_DIR / "poisson_goals_v2.pkl")
    print(f"\n[saved] -> {MODELS_DIR / 'poisson_goals_v2.pkl'}")


if __name__ == "__main__":
    main()