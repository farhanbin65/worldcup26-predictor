"""
Group standings calculator: takes match results (real or simulated) and
produces FIFA-style group tables.

Tiebreaker order implemented: points -> goal difference -> goals scored.
NOT implemented (documented limitation): head-to-head among tied teams,
disciplinary points, drawing of lots. These only matter in rare exact-tie
scenarios; for a Monte Carlo simulation run 10,000 times, omitting them
introduces negligible bias compared to the simplicity gained.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TeamGroupStats:
    team: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        return self.won * 3 + self.drawn

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    def sort_key(self) -> tuple[int, int, int]:
        """Higher is better for all three — used with reverse=True when sorting."""
        return (self.points, self.goal_diff, self.goals_for)


def compute_group_table(
    teams: list[str],
    matches: list[tuple[str, str, int, int]],  # (home, away, home_score, away_score)
) -> list[TeamGroupStats]:
    """
    Build a ranked table for one group from a list of played matches.
    `matches` should contain ALL matches for this group (real + simulated),
    not just real ones — that's the caller's responsibility.
    """
    stats = {team: TeamGroupStats(team=team) for team in teams}

    for home, away, hs, as_ in matches:
        h, a = stats[home], stats[away]
        h.played += 1
        a.played += 1
        h.goals_for += hs
        h.goals_against += as_
        a.goals_for += as_
        a.goals_against += hs

        if hs > as_:
            h.won += 1
            a.lost += 1
        elif hs < as_:
            a.won += 1
            h.lost += 1
        else:
            h.drawn += 1
            a.drawn += 1

    ranked = sorted(stats.values(), key=lambda s: s.sort_key(), reverse=True)
    return ranked


def print_table(group_letter: str, ranked: list[TeamGroupStats]) -> None:
    print(f"\nGroup {group_letter}")
    print(f"{'Team':25s} {'P':>2} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>4} {'Pts':>4}")
    for s in ranked:
        print(f"{s.team:25s} {s.played:2d} {s.won:2d} {s.drawn:2d} {s.lost:2d} "
              f"{s.goals_for:3d} {s.goals_against:3d} {s.goal_diff:+4d} {s.points:4d}")


def main() -> None:
    """Sanity check: build tables using ONLY real results so far (partial)."""
    from src.simulation.tournament_structure import GROUPS
    from src.simulation.results_so_far import RESULTS_SO_FAR

    for group_letter, teams in GROUPS.items():
        group_matches = [
            (r.home, r.away, r.home_score, r.away_score)
            for r in RESULTS_SO_FAR
            if r.group == group_letter
        ]
        if not group_matches:
            continue  # this group hasn't played yet (e.g. I, J, K, L as of June 16)
        ranked = compute_group_table(teams, group_matches)
        print_table(group_letter, ranked)


if __name__ == "__main__":
    main()