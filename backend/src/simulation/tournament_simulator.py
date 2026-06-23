"""
Full tournament simulation: Part 1 — group stage through R32 qualification.

Combines real results + simulated remaining fixtures into final group
tables, determines group winners/runners-up, and selects the 8 best
third-place teams across all 12 groups (with their own tiebreaker rules,
since comparing 3rd-place teams ACROSS different groups needs the same
points -> GD -> goals-scored logic, just applied across group boundaries).

Does NOT yet simulate knockouts — stops at "who qualified for R32 and in
what bracket position." That's verified separately before we add knockouts.
"""

from __future__ import annotations
import numpy as np

from src.simulation.tournament_structure import GROUPS, to_dataset_name
from src.simulation.results_so_far import RESULTS_SO_FAR
from src.simulation.remaining_fixtures import REMAINING_FIXTURES
from src.simulation.group_standings import compute_group_table, TeamGroupStats
from src.simulation.match_simulator import simulate_match
from src.simulation.elo_state import SimulationEloState, load_starting_ratings

# Frozen features (form/rest/h2h) — real current values, NOT simulated
# dynamically. We need a lookup of each team's current feature snapshot.
# Built once from the historical feature table, reused read-only across
# all simulations (only Elo is mutated per-simulation, via SimulationEloState).
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path("data/processed")


def load_frozen_features() -> dict[str, dict]:
    """
    For each WC2026 team, grab their MOST RECENT pre-match feature snapshot
    from the historical dataset (their last actual match's "post-match"
    state, used as a stand-in for "current form" going into the tournament).
    """
    df = pd.read_parquet(PROCESSED_DIR / "matches_features.parquet")
    df = df.sort_values("date")

    snapshots = {}
    all_teams_dataset_names = {
        to_dataset_name(t) for group in GROUPS.values() for t in group
    }

    for team in all_teams_dataset_names:
        # Find this team's most recent match (as home OR away) and grab
        # whichever side's features belong to them.
        home_matches = df[df["home_team"] == team]
        away_matches = df[df["away_team"] == team]

        last_home = home_matches.iloc[-1] if len(home_matches) else None
        last_away = away_matches.iloc[-1] if len(away_matches) else None

        if last_home is not None and (last_away is None or last_home["date"] >= last_away["date"]):
            snapshots[team] = {
                "form_points_5": last_home["home_form_points_5"],
                "form_points_10": last_home["home_form_points_10"],
                "form_goals_for_5": last_home["home_form_goals_for_5"],
                "form_goals_against_5": last_home["home_form_goals_against_5"],
                "rest_days": 14,  # WC2026 group matches are ~3-4 days apart; use a tournament-typical value rather than their pre-WC rest gap
            }
        elif last_away is not None:
            snapshots[team] = {
                "form_points_5": last_away["away_form_points_5"],
                "form_points_10": last_away["away_form_points_10"],
                "form_goals_for_5": last_away["away_form_goals_for_5"],
                "form_goals_against_5": last_away["away_form_goals_against_5"],
                "rest_days": 14,
            }
        else:
            # No history at all (shouldn't happen for WC2026 qualifiers, but defensive)
            snapshots[team] = {
                "form_points_5": 0.5, "form_points_10": 0.5,
                "form_goals_for_5": 1.0, "form_goals_against_5": 1.0,
                "rest_days": 14,
            }
    return snapshots


def simulate_group_stage(
    elo_state: SimulationEloState,
    frozen_features: dict[str, dict],
    rng: np.random.Generator,
) -> dict[str, list[TeamGroupStats]]:
    """
    Simulate all remaining group fixtures, combine with real results,
    return final ranked tables for all 12 groups.
    """
    # Start with real results (converted to dataset team names for Elo,
    # but we keep GROUPS-style names for the standings table since that's
    # what the rest of the UI/bracket logic will display).
    all_matches_by_group: dict[str, list[tuple[str, str, int, int]]] = {
        g: [] for g in GROUPS
    }
    for r in RESULTS_SO_FAR:
        all_matches_by_group[r.group].append((r.home, r.away, r.home_score, r.away_score))

    # Simulate each remaining fixture
    for fx in REMAINING_FIXTURES:
        home_ds = to_dataset_name(fx.home)
        away_ds = to_dataset_name(fx.away)
        feat_h = frozen_features[home_ds]
        feat_a = frozen_features[away_ds]

        hs, as_, outcome = simulate_match(
            fx.home, fx.away,
            home_elo=elo_state.get(home_ds), away_elo=elo_state.get(away_ds),
            home_form_points_5=feat_h["form_points_5"], away_form_points_5=feat_a["form_points_5"],
            home_form_points_10=feat_h["form_points_10"], away_form_points_10=feat_a["form_points_10"],
            home_form_goals_for_5=feat_h["form_goals_for_5"], home_form_goals_against_5=feat_h["form_goals_against_5"],
            away_form_goals_for_5=feat_a["form_goals_for_5"], away_form_goals_against_5=feat_a["form_goals_against_5"],
            home_rest_days=feat_h["rest_days"], away_rest_days=feat_a["rest_days"],
            h2h_home_win_rate=0.5, h2h_matches_played=0,  # simplification: frozen neutral prior for WC fixtures
            rng=rng,
        )

        all_matches_by_group[fx.group].append((fx.home, fx.away, hs, as_))

        # Update THIS simulation's dynamic Elo state
        elo_state.update_after_match(home_ds, away_ds, hs, as_, neutral_venue=True)

    # Build final ranked tables
    tables: dict[str, list[TeamGroupStats]] = {}
    for group_letter, teams in GROUPS.items():
        tables[group_letter] = compute_group_table(teams, all_matches_by_group[group_letter])

    return tables


def select_best_third_place(tables: dict[str, list[TeamGroupStats]]) -> list[tuple[str, str]]:
    """
    Return [(group_letter, team_name), ...] for the 8 best 3rd-place teams
    across all 12 groups, ranked by the same points -> GD -> GF criteria.
    """
    third_placed = []
    for group_letter, ranked in tables.items():
        third = ranked[2]  # index 2 = 3rd position
        third_placed.append((group_letter, third))

    third_placed_sorted = sorted(
        third_placed, key=lambda gt: gt[1].sort_key(), reverse=True
    )
    return [(g, t.team) for g, t in third_placed_sorted[:8]]


def print_qualification_summary(tables: dict[str, list[TeamGroupStats]], best_thirds: list[tuple[str, str]]) -> None:
    print("=== Group winners and runners-up ===")
    for g, ranked in tables.items():
        print(f"  Group {g}: 1st={ranked[0].team:20s} 2nd={ranked[1].team:20s} "
              f"3rd={ranked[2].team:20s} 4th={ranked[3].team}")

    print("\n=== 8 best third-place teams (qualify for R32) ===")
    for g, team in best_thirds:
        print(f"  Group {g}: {team}")

    qualifying_groups = {g for g, _ in best_thirds}
    print(f"\n[check] Groups producing a qualifying 3rd-place team: {sorted(qualifying_groups)}")


if __name__ == "__main__":
    rng = np.random.default_rng(seed=7)
    starting_elo = load_starting_ratings()
    frozen_features = load_frozen_features()

    elo_state = SimulationEloState(starting_elo)
    tables = simulate_group_stage(elo_state, frozen_features, rng)
    best_thirds = select_best_third_place(tables)

    print_qualification_summary(tables, best_thirds)