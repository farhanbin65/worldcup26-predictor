"""
Exploratory analysis of the feature table before any modelling.

Goal: confirm our features actually separate match outcomes,
understand class imbalance, and check for redundant features.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")


def elo_vs_outcome(df: pd.DataFrame) -> None:
    """
    Bucket elo_diff into bins and show outcome distribution per bin.
    If Elo carries signal, home win rate should rise sharply with elo_diff.
    """
    bins = [-2000, -200, -100, -50, 0, 50, 100, 200, 2000]
    labels = ["<-200", "-200..-100", "-100..-50", "-50..0",
              "0..50", "50..100", "100..200", ">200"]
    df = df.copy()
    df["elo_bucket"] = pd.cut(df["elo_diff"], bins=bins, labels=labels)

    print("=== Home win rate by Elo difference bucket ===")
    table = (
        df.groupby("elo_bucket")["outcome"]
        .apply(lambda s: (s == "H").mean())
        .round(3)
    )
    counts = df["elo_bucket"].value_counts().sort_index()
    summary = pd.DataFrame({"home_win_rate": table, "n_matches": counts})
    print(summary)
    print()


def class_balance(df: pd.DataFrame) -> None:
    print("=== Outcome class balance ===")
    print(df["outcome"].value_counts(normalize=True).round(3))
    print()


def feature_correlations(df: pd.DataFrame) -> None:
    """Check redundancy between window sizes (5 vs 10) and Elo vs form."""
    cols = [
        "elo_diff", "home_elo_pre", "away_elo_pre",
        "home_form_points_5", "home_form_points_10",
        "away_form_points_5", "away_form_points_10",
        "home_form_goals_for_5", "home_form_goals_for_10",
    ]
    print("=== Feature correlation matrix ===")
    print(df[cols].corr().round(2))
    print()


def recent_data_check(df: pd.DataFrame) -> None:
    """
    We trained Elo/form on ALL history, but WC2026 matches need
    to be predicted using only pre-tournament knowledge. Sanity-check
    how much data exists right up to the tournament start.
    """
    recent = df[df["date"] >= "2025-01-01"]
    print(f"=== Matches in 2025-2026 (pre/early-tournament): {len(recent):,} ===")
    print(recent["tournament"].value_counts().head(8))


def main() -> None:
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    print(f"[loaded] {len(df):,} rows\n")

    class_balance(df)
    elo_vs_outcome(df)
    feature_correlations(df)
    recent_data_check(df)


if __name__ == "__main__":
    main()