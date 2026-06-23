"""
The full Monte Carlo tournament engine: runs N complete WC2026 simulations
end-to-end, tallying results into probabilities the website can display.

This is the final assembly of every verified piece built in this phase:
group stage simulation, third-place qualification, R32 bracket resolution,
and knockout simulation through to a champion.
"""

from __future__ import annotations
import time
import numpy as np
import json
from pathlib import Path
from collections import Counter, defaultdict

from src.simulation.tournament_simulator import (
    simulate_group_stage, select_best_third_place,
    load_frozen_features, load_starting_ratings,
)
from src.simulation.elo_state import SimulationEloState
from src.simulation.r32_resolver import resolve_r32_matchups
from src.simulation.knockout_simulator import simulate_knockout_bracket
from src.simulation.tournament_structure import ALL_TEAMS

OUTPUT_DIR = Path("data/processed")


def run_monte_carlo(n_simulations: int, seed: int = 0) -> dict:
    """Run N full tournament simulations, return aggregated probabilities."""
    frozen_features = load_frozen_features()
    starting_elo = load_starting_ratings()

    champion_counts: Counter[str] = Counter()
    final_counts: Counter[str] = Counter()       # reached final (incl. champion)
    semifinal_counts: Counter[str] = Counter()    # reached SF (incl. further)
    qf_counts: Counter[str] = Counter()
    r32_counts: Counter[str] = Counter()          # qualified for knockout stage at all

    start = time.time()
    for i in range(n_simulations):
        rng = np.random.default_rng(seed=seed + i)
        elo_state = SimulationEloState(starting_elo)

        tables = simulate_group_stage(elo_state, frozen_features, rng)
        best_thirds = select_best_third_place(tables)
        matchups = resolve_r32_matchups(tables, best_thirds)
        results = simulate_knockout_bracket(matchups, elo_state, frozen_features, rng)

        for team in results["R32_participants"]:
            r32_counts[team] += 1
        for team in results["QF_participants"]:
            qf_counts[team] += 1
        for team in results["SF_participants"]:
            semifinal_counts[team] += 1
        for team in results["Final_participants"]:
            final_counts[team] += 1
        champion_counts[results["Final"][0]] += 1

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start
            print(f"  [{i+1}/{n_simulations}] {elapsed:.1f}s elapsed")

    elapsed = time.time() - start
    print(f"\n[done] {n_simulations} simulations in {elapsed:.1f}s "
          f"({elapsed/n_simulations*1000:.1f}ms/sim)")

    probabilities = {}
    for team in ALL_TEAMS:
        probabilities[team] = {
            "champion_pct": round(champion_counts.get(team, 0) / n_simulations * 100, 2),
            "final_pct": round(final_counts.get(team, 0) / n_simulations * 100, 2),
            "semifinal_pct": round(semifinal_counts.get(team, 0) / n_simulations * 100, 2),
            "quarterfinal_pct": round(qf_counts.get(team, 0) / n_simulations * 100, 2),
            "round_of_32_pct": round(r32_counts.get(team, 0) / n_simulations * 100, 2),
        }

    return {
        "n_simulations": n_simulations,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "probabilities": probabilities,
    }


def print_top_contenders(output: dict, top_n: int = 15) -> None:
    sorted_teams = sorted(
        output["probabilities"].items(),
        key=lambda kv: kv[1]["champion_pct"],
        reverse=True,
    )
    print(f"\n=== Top {top_n} title contenders ===")
    print(f"{'Team':20s} {'Champion%':>10s} {'Final%':>8s} {'SF%':>6s} {'QF%':>6s} {'R32%':>6s}")
    for team, stats in sorted_teams[:top_n]:
        print(f"{team:20s} {stats['champion_pct']:10.2f} {stats['final_pct']:8.2f} "
              f"{stats['semifinal_pct']:6.2f} {stats['quarterfinal_pct']:6.2f} {stats['round_of_32_pct']:6.2f}")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000  # default 1000 for a quick first run

    output = run_monte_carlo(n_simulations=n, seed=42)
    print_top_contenders(output)

    out_path = OUTPUT_DIR / "tournament_probabilities.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[saved] -> {out_path}")