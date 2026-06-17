"""
WC2026 Round of 32 bracket mapping — the official FIFA lookup table for
how group positions map to knockout fixtures.

WHY THIS IS HARD: 8 of the 32 Round of 32 slots are filled by "best
third-place teams", and WHICH third-place teams qualify depends on actual
group results (not known until group stage ends). FIFA pre-published which
GROUP COMBINATIONS map to which bracket slot, e.g. "Group E winner plays
the third-place team from whichever of groups A/B/C/D/F finished 3rd
(if that group's 3rd-placer is among the best 8)". If group E's own
3rd-placer is one of the best 8, a substitution rule kicks in (handled
in the simulator, not here) since a team can't play itself.

This file encodes the structure exactly as published; the simulator
resolves the "which actual team" question after group stage simulation.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class R32Fixture:
    slot: int
    description: str          # human-readable, matches the published bracket
    home_rule: str             # e.g. "A2" (runner-up of A), "C1" (winner of C), "ABCDF3" (3rd place from one of these groups)
    away_rule: str


# Reading the rules: "X1" = winner of group X, "X2" = runner-up of group X,
# "XYZ3" = the qualifying 3rd-place team from group X, Y, or Z (whichever
# of those actually produced one of the 8 best 3rd-place teams).
R32_BRACKET: list[R32Fixture] = [
    R32Fixture(1, "Group A runners-up vs Group B runners-up", "A2", "B2"),
    R32Fixture(2, "Group C winners vs Group F runners-up", "C1", "F2"),
    R32Fixture(3, "Group E winners vs ABCDF 3rd place", "E1", "ABCDF3"),
    R32Fixture(4, "Group F winners vs Group C runners-up", "F1", "C2"),
    R32Fixture(5, "Group E runners-up vs Group I runners-up", "E2", "I2"),
    R32Fixture(6, "Group I winners vs CDFGH 3rd place", "I1", "CDFGH3"),
    R32Fixture(7, "Group A winners vs CEFHI 3rd place", "A1", "CEFHI3"),
    R32Fixture(8, "Group L winners vs EHIJK 3rd place", "L1", "EHIJK3"),
    R32Fixture(9, "Group G winners vs AEHIJ 3rd place", "G1", "AEHIJ3"),
    R32Fixture(10, "Group D winners vs BEFIJ 3rd place", "D1", "BEFIJ3"),
    R32Fixture(11, "Group H winners vs Group J runners-up", "H1", "J2"),
    R32Fixture(12, "Group K runners-up vs Group L runners-up", "K2", "L2"),
    R32Fixture(13, "Group B winners vs EFGIJ 3rd place", "B1", "EFGIJ3"),
    R32Fixture(14, "Group D runners-up vs Group G runners-up", "D2", "G2"),
    R32Fixture(15, "Group J winners vs Group H runners-up", "J1", "H2"),
    R32Fixture(16, "Group K winners vs DEIJL 3rd place", "K1", "DEIJL3"),
]


def print_summary() -> None:
    print(f"[bracket] {len(R32_BRACKET)} Round of 32 fixtures defined")
    for fx in R32_BRACKET:
        print(f"  Slot {fx.slot:2d}: {fx.description}")


if __name__ == "__main__":
    print_summary()