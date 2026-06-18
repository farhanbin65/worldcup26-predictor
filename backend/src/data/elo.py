"""
Compute Elo ratings for every international team from match history.

This is the foundational feature for the whole model. Two outputs:
  1) A time-series of Elo ratings per team (for any historical lookup)
  2) An augmented matches dataframe with pre-match Elo for both sides
     (this is what we'll train on — pre-match, never post-match, no leakage)
"""

from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import math
import pandas as pd

PROCESSED_DIR = Path("data/processed")

# --- Tunable constants (defensible defaults from football Elo literature) ---
INITIAL_RATING = 1500.0       # Every team starts here on first appearance
HOME_ADVANTAGE = 65.0         # Elo points added to home team (when not neutral)
BASE_K = 30.0                 # Base learning rate

# Tournament weight multipliers on K (higher = match matters more)
TOURNAMENT_WEIGHTS = {
    "FIFA World Cup": 2.00,
    "FIFA World Cup qualification": 1.50,
    "UEFA Euro": 1.75,
    "UEFA Euro qualification": 1.25,
    "Copa América": 1.75,
    "African Cup of Nations": 1.50,
    "AFC Asian Cup": 1.50,
    "Confederations Cup": 1.50,
    "UEFA Nations League": 1.30,
    "Friendly": 1.00,
}
DEFAULT_WEIGHT = 1.10  # Anything else (continental qualifiers, minor cups)


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability-like expected score for A vs B. See formula above."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def goal_diff_multiplier(goal_diff: int) -> float:
    """
    Scale K by margin of victory. Same shape eloratings.net uses:
      diff=1 -> 1.0
      diff=2 -> 1.5
      diff=3+ -> 1.75 + (diff-3)/8
    """
    d = abs(goal_diff)
    if d <= 1:
        return 1.0
    if d == 2:
        return 1.5
    return 1.75 + (d - 3) / 8.0


def tournament_weight(name: str) -> float:
    return TOURNAMENT_WEIGHTS.get(name, DEFAULT_WEIGHT)


def actual_score(outcome: str) -> float:
    """Map H/D/A to home team's score in [0,1]."""
    return {"H": 1.0, "D": 0.5, "A": 0.0}[outcome]


def compute_elo(matches: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Walk through matches in chronological order, updating Elo after each.

    Returns:
      enriched_matches: original df + pre-match elo columns + win probability
      final_ratings:    dict of {team: final_elo} after all matches processed
    """
    ratings: dict[str, float] = defaultdict(lambda: INITIAL_RATING)

    # Pre-allocate lists — faster than appending to dataframe rows
    home_elo_pre, away_elo_pre, home_win_prob = [], [], []

    for row in matches.itertuples(index=False):
        home, away = row.home_team, row.away_team
        r_home = ratings[home]
        r_away = ratings[away]

        # Apply home advantage only when not at a neutral venue
        is_neutral = bool(getattr(row, "neutral", False))
        r_home_eff = r_home + (0.0 if is_neutral else HOME_ADVANTAGE)

        # Pre-match snapshot (this is what we'll feed the ML model later)
        exp_home = expected_score(r_home_eff, r_away)
        home_elo_pre.append(r_home)
        away_elo_pre.append(r_away)
        home_win_prob.append(exp_home)

        # Compute the rating change
        s_home = actual_score(row.outcome)
        k = BASE_K * tournament_weight(row.tournament) * goal_diff_multiplier(row.goal_diff)
        delta = k * (s_home - exp_home)

        # Symmetric update: what home gains, away loses
        ratings[home] = r_home + delta
        ratings[away] = r_away - delta

    enriched = matches.copy()
    enriched["home_elo_pre"] = home_elo_pre
    enriched["away_elo_pre"] = away_elo_pre
    enriched["home_win_prob_elo"] = home_win_prob   # naive elo-only baseline
    enriched["elo_diff"] = enriched["home_elo_pre"] - enriched["away_elo_pre"]

    return enriched, dict(ratings)


def main() -> None:
    matches = pd.read_parquet(PROCESSED_DIR / "matches_clean.parquet")
    print(f"[loaded] {len(matches):,} matches")

    enriched, final_ratings = compute_elo(matches)

    out_matches = PROCESSED_DIR / "matches_with_elo.parquet"
    enriched.to_parquet(out_matches, index=False)
    print(f"[saved] matches with elo -> {out_matches}")

    ratings_df = (
        pd.DataFrame({"team": list(final_ratings.keys()),
                      "elo": list(final_ratings.values())})
        .sort_values("elo", ascending=False)
        .reset_index(drop=True)
    )
    out_ratings = PROCESSED_DIR / "elo_current.parquet"
    ratings_df.to_parquet(out_ratings, index=False)
    print(f"[saved] current ratings -> {out_ratings}")

    print("\n=== Top 20 by Elo (as of latest match in dataset) ===")
    print(ratings_df.head(20).to_string(index=False))
    print("\n=== Bottom 5 (sanity check) ===")
    print(ratings_df.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()