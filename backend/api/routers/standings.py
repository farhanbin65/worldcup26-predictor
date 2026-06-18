"""
Group standings endpoint.

Reuses compute_group_table() from Phase 8 — same function already
verified against real WC2026 results (Group D check: USA 4-1 Paraguay
correctly producing GD=+3, ranked above Australia's GD=+2). No new logic
here, just exposing it over HTTP.
"""

from __future__ import annotations
from fastapi import APIRouter

from src.simulation.tournament_structure import GROUPS
from src.simulation.results_so_far import RESULTS_SO_FAR
from src.simulation.group_standings import compute_group_table

router = APIRouter(prefix="/standings", tags=["standings"])


@router.get("/")
def get_all_standings():
    """Returns current group tables for all 12 groups, using real results so far."""
    matches_by_group: dict[str, list[tuple[str, str, int, int]]] = {g: [] for g in GROUPS}
    for r in RESULTS_SO_FAR:
        matches_by_group[r.group].append((r.home, r.away, r.home_score, r.away_score))

    response = {}
    for group_letter, teams in GROUPS.items():
        ranked = compute_group_table(teams, matches_by_group[group_letter])
        response[group_letter] = [
            {
                "team": s.team, "played": s.played,
                "won": s.won, "drawn": s.drawn, "lost": s.lost,
                "goals_for": s.goals_for, "goals_against": s.goals_against,
                "goal_diff": s.goal_diff, "points": s.points,
            }
            for s in ranked
        ]

    return {"groups": response}


@router.get("/{group_letter}")
def get_group_standings(group_letter: str):
    """Returns the table for a single group, e.g. /standings/D"""
    group_letter = group_letter.upper()
    if group_letter not in GROUPS:
        return {"error": f"Group '{group_letter}' not found. Valid groups: {sorted(GROUPS.keys())}"}

    teams = GROUPS[group_letter]
    matches = [
        (r.home, r.away, r.home_score, r.away_score)
        for r in RESULTS_SO_FAR
        if r.group == group_letter
    ]
    ranked = compute_group_table(teams, matches)

    return {
        "group": group_letter,
        "table": [
            {
                "team": s.team, "played": s.played,
                "won": s.won, "drawn": s.drawn, "lost": s.lost,
                "goals_for": s.goals_for, "goals_against": s.goals_against,
                "goal_diff": s.goal_diff, "points": s.points,
            }
            for s in ranked
        ],
    }