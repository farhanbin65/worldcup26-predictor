"""
Per-simulation Elo state tracker.

Each simulated tournament run gets its OWN independent copy of every
team's Elo rating, seeded from real current values. As simulated matches
are "played" (group stage AND knockouts), this tracker updates ratings
using the EXACT SAME formula as src/data/elo.py — same expected_score(),
same goal_diff_multiplier(), same home advantage constant — so the dynamic
in-simulation Elo means the same thing as the historical Elo it's based on.

Critical: a fresh SimulationEloState must be created for EVERY simulation
run. Reusing one across simulations would let simulation #1's randomness
leak into simulation #2's starting ratings — a subtle but serious bug.
"""

from __future__ import annotations
import pandas as pd
from pathlib import Path

from src.data.elo import (
    expected_score,
    goal_diff_multiplier,
    tournament_weight,
    actual_score,
    HOME_ADVANTAGE,
    BASE_K,
)

PROCESSED_DIR = Path("data/processed")

# WC2026 matches use the FIFA World Cup weight (2.00x) — same constant
# already defined in elo.py's TOURNAMENT_WEIGHTS dict, reused here for consistency.
WC_TOURNAMENT_NAME = "FIFA World Cup"


class SimulationEloState:
    """Holds a mutable, per-simulation copy of every team's current Elo."""

    def __init__(self, starting_ratings: dict[str, float]):
        # Copy, not reference — each simulation must be fully independent.
        self.ratings: dict[str, float] = dict(starting_ratings)

    def get(self, team: str) -> float:
        return self.ratings.get(team, 1500.0)  # 1500 fallback for any
                                                  # team somehow missing from
                                                  # historical data (shouldn't
                                                  # happen after our name-alias
                                                  # validation, but defensive)

    def update_after_match(
        self, home_team: str, away_team: str,
        home_score: int, away_score: int,
        neutral_venue: bool = False,
    ) -> None:
        """
        Apply one match result to THIS simulation's Elo state.
        Mirrors compute_elo() in src/data/elo.py exactly, but operates on
        a single match rather than walking a full historical dataframe.
        """
        r_home = self.get(home_team)
        r_away = self.get(away_team)
        r_home_eff = r_home + (0.0 if neutral_venue else HOME_ADVANTAGE)

        exp_home = expected_score(r_home_eff, r_away)

        if home_score > away_score:
            outcome = "H"
        elif home_score < away_score:
            outcome = "A"
        else:
            outcome = "D"

        s_home = actual_score(outcome)
        goal_diff = home_score - away_score
        k = BASE_K * tournament_weight(WC_TOURNAMENT_NAME) * goal_diff_multiplier(goal_diff)
        delta = k * (s_home - exp_home)

        self.ratings[home_team] = r_home + delta
        self.ratings[away_team] = r_away - delta


def load_starting_ratings() -> dict[str, float]:
    """Load real current Elo ratings to seed every simulation's starting point."""
    df = pd.read_parquet(PROCESSED_DIR / "elo_current.parquet")
    return dict(zip(df["team"], df["elo"]))


if __name__ == "__main__":
    # Quick sanity test: simulate Austria beating Jordan 3-1 (neutral venue,
    # since WC2026 matches are technically neutral for most teams), confirm
    # Austria's Elo rises and Jordan's falls by the same magnitude.
    starting = load_starting_ratings()

    from src.simulation.tournament_structure import to_dataset_name
    austria_key = to_dataset_name("Austria")
    jordan_key = to_dataset_name("Jordan")

    state = SimulationEloState(starting)
    before_austria = state.get(austria_key)
    before_jordan = state.get(jordan_key)
    print(f"Before: Austria={before_austria:.2f}  Jordan={before_jordan:.2f}")

    state.update_after_match(austria_key, jordan_key, 3, 1, neutral_venue=True)

    after_austria = state.get(austria_key)
    after_jordan = state.get(jordan_key)
    print(f"After:  Austria={after_austria:.2f}  Jordan={after_jordan:.2f}")

    austria_gain = after_austria - before_austria
    jordan_loss = before_jordan - after_jordan
    print(f"\nAustria gained {austria_gain:.2f}, Jordan lost {jordan_loss:.2f}")
    print(f"Symmetric? {abs(austria_gain - jordan_loss) < 0.001}")