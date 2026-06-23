"""
Extends tournament_simulator.py: resolves the full R32 lineup by combining
group stage results with the third-place assignment rule.

This is PURE PLUMBING — no new modeling logic, just connecting already-
verified pieces: simulate_group_stage() -> select_best_third_place() ->
assign_third_place_opponents() -> a complete list of 16 R32 matchups.
"""

from __future__ import annotations
from src.simulation.r32_bracket import (
    FIXED_R32_MATCHES, THIRD_PLACE_R32_MATCHES, assign_third_place_opponents
)
from src.simulation.group_standings import TeamGroupStats


def resolve_r32_matchups(
    tables: dict[str, list[TeamGroupStats]],
    best_thirds: list[tuple[str, str]],  # [(group_letter, team_name), ...]
) -> list[tuple[str, str, int]]:
    """
    Returns [(team_a, team_b, slot_number), ...] for all 16 R32 matches.
    `tables[group][0]` = winner, `tables[group][1]` = runner-up.
    """
    matchups: list[tuple[str, str, int]] = []

    # Fixed matches: just look up winner/runner-up directly from tables
    for fx in FIXED_R32_MATCHES:
        team_a = _resolve_rule(fx.home_rule, tables)
        team_b = _resolve_rule(fx.away_rule, tables)
        matchups.append((team_a, team_b, fx.slot))

    # Third-place matches: winner is fixed, opponent comes from assignment
    third_place_opponents = assign_third_place_opponents(best_thirds)
    for fx in THIRD_PLACE_R32_MATCHES:
        team_a = _resolve_rule(fx.home_rule, tables)
        team_b = third_place_opponents[fx.slot]
        matchups.append((team_a, team_b, fx.slot))

    return matchups


def _resolve_rule(rule: str, tables: dict[str, list[TeamGroupStats]]) -> str:
    """'A1' -> winner of group A, 'B2' -> runner-up of group B."""
    group_letter, position = rule[0], int(rule[1])
    return tables[group_letter][position - 1].team


def print_r32_matchups(matchups: list[tuple[str, str, int]]) -> None:
    print("=== Round of 32 matchups ===")
    for team_a, team_b, slot in sorted(matchups, key=lambda m: m[2]):
        print(f"  Match {slot}: {team_a:25s} vs {team_b}")


if __name__ == "__main__":
    import numpy as np
    from src.simulation.tournament_simulator import (
        simulate_group_stage, select_best_third_place,
        load_frozen_features, load_starting_ratings,
    )
    from src.simulation.elo_state import SimulationEloState

    rng = np.random.default_rng(seed=1)
    frozen_features = load_frozen_features()
    starting_elo = load_starting_ratings()
    elo_state = SimulationEloState(starting_elo)

    tables = simulate_group_stage(elo_state, frozen_features, rng)
    best_thirds = select_best_third_place(tables)
    matchups = resolve_r32_matchups(tables, best_thirds)

    print_r32_matchups(matchups)

    # Sanity check: exactly 16 matches, 32 distinct teams, no duplicates
    teams_in_bracket = [t for m in matchups for t in (m[0], m[1])]
    print(f"\n[check] {len(matchups)} matches, {len(teams_in_bracket)} team slots, "
          f"{len(set(teams_in_bracket))} distinct teams")