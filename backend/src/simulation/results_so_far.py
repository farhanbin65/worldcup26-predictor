"""
WC2026 group stage results, recorded so far (as of 2026-06-16).

MAINTENANCE NOTE: this file must be updated by hand as the tournament
progresses, since no reliable structured API exists for WC2026 fixtures.
This is a known, documented limitation — not an oversight. Source: ESPN
fixtures page, cross-checked match by match.

Each entry uses team names as they appear in tournament_structure.GROUPS
(current/FIFA names) — NOT yet translated to historical dataset names.
That translation happens at simulation time via to_dataset_name().
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    date: str
    group: str
    home: str
    away: str
    home_score: int
    away_score: int


RESULTS_SO_FAR: list[MatchResult] = [
    MatchResult("2026-06-11", "A", "Mexico", "South Africa", 2, 0),
    MatchResult("2026-06-11", "A", "South Korea", "Czechia", 2, 1),
    MatchResult("2026-06-12", "B", "Canada", "Bosnia and Herzegovina", 1, 1),
    MatchResult("2026-06-12", "D", "United States", "Paraguay", 4, 1),
    MatchResult("2026-06-13", "B", "Qatar", "Switzerland", 1, 1),
    MatchResult("2026-06-13", "C", "Brazil", "Morocco", 1, 1),
    MatchResult("2026-06-13", "C", "Haiti", "Scotland", 0, 1),
    MatchResult("2026-06-13", "D", "Australia", "Turkiye", 2, 0),
    MatchResult("2026-06-14", "E", "Germany", "Curacao", 7, 1),
    MatchResult("2026-06-14", "F", "Netherlands", "Japan", 2, 2),
    MatchResult("2026-06-14", "E", "Ivory Coast", "Ecuador", 1, 0),
    MatchResult("2026-06-14", "F", "Sweden", "Tunisia", 5, 1),
    MatchResult("2026-06-15", "H", "Spain", "Cape Verde", 0, 0),
    MatchResult("2026-06-15", "G", "Belgium", "Egypt", 1, 1),
    MatchResult("2026-06-15", "H", "Saudi Arabia", "Uruguay", 1, 1),
    MatchResult("2026-06-15", "G", "Iran", "New Zealand", 2, 2),
    # 2026-06-16 matches (France-Senegal, Iraq-Norway, Argentina-Algeria,
    # Austria-Jordan) were in progress/same-day as this data was compiled —
    # ADD THEM HERE once final, and continue adding as the tournament goes.
]


def print_summary() -> None:
    print(f"[results] {len(RESULTS_SO_FAR)} matches recorded so far")
    by_group: dict[str, int] = {}
    for r in RESULTS_SO_FAR:
        by_group[r.group] = by_group.get(r.group, 0) + 1
    for g in sorted(by_group):
        print(f"  Group {g}: {by_group[g]} match(es) played")


if __name__ == "__main__":
    print_summary()