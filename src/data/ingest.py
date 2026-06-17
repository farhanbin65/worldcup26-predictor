"""
Ingest international match results from martj42/international_results.

We pull the raw CSV directly from GitHub rather than committing a snapshot.
Tradeoff: needs internet on first run, but always reflects latest data.
For a portfolio project this is fine; for production we'd vendor it.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

# Constants up top — never magic strings in the middle of functions
RESULTS_URL = (
    "https://raw.githubusercontent.com/martj42/"
    "international_results/master/results.csv"
)
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")


def download_raw(force: bool = False) -> Path:
    """Download the raw results CSV. Cache to disk; only re-download if forced."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "results.csv"
    if out_path.exists() and not force:
        print(f"[cache hit] {out_path}")
        return out_path
    print(f"[downloading] {RESULTS_URL}")
    df = pd.read_csv(RESULTS_URL)
    df.to_csv(out_path, index=False)
    print(f"[saved] {len(df):,} rows -> {out_path}")
    return out_path


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the raw match results.

    Decisions made here (each one defensible in interview):
    - Parse date to datetime so we can sort chronologically (critical for Elo).
    - Drop rows with missing scores (can't train on unknown outcomes).
    - Add `outcome` column: 'H', 'D', 'A' from home team's perspective.
    - Add `goal_diff` (home - away) for later feature engineering.
    - Keep neutral-venue flag — we'll use it to dampen home advantage.
    - Sort by date ascending — Elo updates depend on chronological order.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_score", "away_score"])
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["goal_diff"] = df["home_score"] - df["away_score"]

    def _outcome(gd: int) -> str:
        if gd > 0:
            return "H"
        if gd < 0:
            return "A"
        return "D"

    df["outcome"] = df["goal_diff"].apply(_outcome)
    df = df.sort_values("date").reset_index(drop=True)
    return df


def summarise(df: pd.DataFrame) -> None:
    """Print a quick health check. Always inspect your data."""
    print("\n=== Dataset summary ===")
    print(f"Rows:          {len(df):,}")
    print(f"Date range:    {df['date'].min().date()} -> {df['date'].max().date()}")
    print(f"Unique teams:  {pd.concat([df['home_team'], df['away_team']]).nunique()}")
    print("\nOutcome distribution (home perspective):")
    print(df["outcome"].value_counts(normalize=True).round(3))
    print("\nTop 5 tournaments by count:")
    print(df["tournament"].value_counts().head())


def main() -> None:
    raw_path = download_raw()
    df_raw = pd.read_csv(raw_path)
    df = clean(df_raw)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "matches_clean.parquet"
    df.to_parquet(out, index=False)
    print(f"\n[saved clean] -> {out}")
    summarise(df)


if __name__ == "__main__":
    main()