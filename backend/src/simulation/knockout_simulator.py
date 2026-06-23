"""
Knockout stage simulator: R32 -> R16 -> QF -> SF -> Final.

Each round: simulate every match using the same models as group stage.
If outcome is a draw, resolve via penalty shootout (modeled as a near
coin-flip — well-documented in football analytics that shootout outcomes
are close to 50/50 regardless of pre-match team strength, unlike 90-minute
play). Elo updates dynamically after every knockout match too, same as
group stage (per the "yes, both" decision).
"""

from __future__ import annotations
import numpy as np

from src.simulation.tournament_structure import to_dataset_name
from src.simulation.match_simulator import simulate_match
from src.simulation.elo_state import SimulationEloState


def simulate_knockout_match(
    team_a: str, team_b: str,
    elo_state: SimulationEloState,
    frozen_features: dict[str, dict],
    rng: np.random.Generator,
) -> str:
    """Returns the winning team name. Draws resolved via penalty shootout."""
    a_ds = to_dataset_name(team_a)
    b_ds = to_dataset_name(team_b)
    feat_a = frozen_features[a_ds]
    feat_b = frozen_features[b_ds]

    hs, as_, outcome = simulate_match(
        team_a, team_b,
        home_elo=elo_state.get(a_ds), away_elo=elo_state.get(b_ds),
        home_form_points_5=feat_a["form_points_5"], away_form_points_5=feat_b["form_points_5"],
        home_form_points_10=feat_a["form_points_10"], away_form_points_10=feat_b["form_points_10"],
        home_form_goals_for_5=feat_a["form_goals_for_5"], home_form_goals_against_5=feat_a["form_goals_against_5"],
        away_form_goals_for_5=feat_b["form_goals_for_5"], away_form_goals_against_5=feat_b["form_goals_against_5"],
        home_rest_days=4, away_rest_days=4,  # knockouts are tightly spaced
        h2h_home_win_rate=0.5, h2h_matches_played=0,
        rng=rng,
    )

    # Update dynamic Elo regardless of how the match is ultimately decided
    elo_state.update_after_match(a_ds, b_ds, hs, as_, neutral_venue=True)

    if outcome == "H":
        return team_a
    if outcome == "A":
        return team_b

    # Draw -> penalty shootout, modeled as near coin-flip with a SLIGHT
    # tilt toward the stronger team (documented: shootouts are close to
    # 50/50, not exactly 50/50 - we use a mild 52/48-style tilt based on
    # Elo, reflecting marginal goalkeeper/composure effects without
    # overclaiming precision here).
    elo_diff = elo_state.get(a_ds) - elo_state.get(b_ds)
    shootout_prob_a = 0.5 + np.clip(elo_diff / 4000, -0.05, 0.05)
    return team_a if rng.random() < shootout_prob_a else team_b


def simulate_knockout_bracket(
    r32_matchups: list[tuple[str, str, int]],
    elo_state: SimulationEloState,
    frozen_features: dict[str, dict],
    rng: np.random.Generator,
) -> dict[str, list[str]]:
    current_round = [(a, b) for a, b, _slot in sorted(r32_matchups, key=lambda m: m[2])]
    round_names = ["R32", "R16", "QF", "SF", "Final"]
    results: dict[str, list[str]] = {}

    for round_name in round_names:
        # Capture PARTICIPANTS (both teams in every match this round) BEFORE
        # resolving winners. "Participated in QF" != "won QF" — these are
        # genuinely different facts and both matter for reporting.
        participants = [team for pair in current_round for team in pair]
        results[f"{round_name}_participants"] = participants

        winners = []
        for team_a, team_b in current_round:
            winner = simulate_knockout_match(team_a, team_b, elo_state, frozen_features, rng)
            winners.append(winner)
        results[round_name] = winners  # winners of this round

        current_round = [
            (winners[i], winners[i + 1]) for i in range(0, len(winners) - 1, 2)
        ]
        if len(winners) == 1:
            break

    return results

if __name__ == "__main__":
    from src.simulation.tournament_simulator import (
        simulate_group_stage, select_best_third_place,
        load_frozen_features, load_starting_ratings,
    )
    from src.simulation.r32_resolver import resolve_r32_matchups

    rng = np.random.default_rng(seed=1)
    frozen_features = load_frozen_features()
    starting_elo = load_starting_ratings()
    elo_state = SimulationEloState(starting_elo)

    tables = simulate_group_stage(elo_state, frozen_features, rng)
    best_thirds = select_best_third_place(tables)
    matchups = resolve_r32_matchups(tables, best_thirds)

    results = simulate_knockout_bracket(matchups, elo_state, frozen_features, rng)

    for round_name, winners in results.items():
        print(f"{round_name}: {winners}")

    champion = results["Final"][0]
    print(f"\n🏆 Champion: {champion}")