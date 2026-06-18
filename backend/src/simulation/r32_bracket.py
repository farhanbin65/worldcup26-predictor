"""
WC2026 Round of 32 bracket — fixed matches verified against Wikipedia's
official bracket diagram (sourced from FIFA's Annex C regulations), plus
a documented simplified rule for the 8 third-place-team slots.

ACCURACY NOTE: the 8 fixed group-winner/runner-up slots below (e.g. "A2 vs
B2") are taken directly from FIFA's published bracket structure and are
NOT subject to the third-place complexity — these are exactly correct
regardless of which third-place teams qualify.

The 8 slots involving a "best third-place team" use a SIMPLIFIED
assignment rule rather than FIFA's official 495-combination Annex C table.
Reason: Annex C's raw column encoding could not be reliably parsed with
confidence from available sources without risking a silently incorrect
mapping. A wrong simplified rule, clearly labeled as such, is safer and
more honest than a wrong "official" table presented as authoritative.

SIMPLIFIED RULE USED: each of the 8 fixed group-winner slots that requires
a third-place opponent (E, I, A, L, G, D, B, K — see FIXED_R32_MATCHES) is
matched against the BEST-RANKED remaining qualifying third-place team that
is NOT from that same group (group winners never face their own group's
3rd-placer, consistent with FIFA's stated opponent-separation principle).
Assignment proceeds in bracket-slot order, consuming the best available
qualifier each time. This preserves the principle (no immediate group
rematches, toughest 3rd-place teams matched against winners) without
claiming exact official accuracy.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class R32Fixture:
    slot: int
    description: str
    home_rule: str   # "X1" = winner of group X, "X2" = runner-up of group X, "THIRD" = resolved dynamically
    away_rule: str


# Matches with NO third-place involvement — taken directly from the
# official bracket diagram, 100% fixed regardless of which 3rd-placers qualify.
FIXED_R32_MATCHES: list[R32Fixture] = [
    R32Fixture(73, "Runner-up A vs Runner-up B", "A2", "B2"),
    R32Fixture(75, "Winner F vs Runner-up C", "F1", "C2"),
    R32Fixture(76, "Winner C vs Runner-up F", "C1", "F2"),
    R32Fixture(78, "Runner-up E vs Runner-up I", "E2", "I2"),
    R32Fixture(83, "Runner-up K vs Runner-up L", "K2", "L2"),
    R32Fixture(84, "Winner H vs Runner-up J", "H1", "J2"),
    R32Fixture(86, "Winner J vs Runner-up H", "J1", "H2"),
    R32Fixture(88, "Runner-up D vs Runner-up G", "D2", "G2"),
]

# Matches requiring a third-place team — group winner is fixed, opponent
# resolved via the simplified rule documented above.
THIRD_PLACE_R32_MATCHES: list[R32Fixture] = [
    R32Fixture(74, "Winner E vs Best 3rd place", "E1", "THIRD"),
    R32Fixture(77, "Winner I vs Best 3rd place", "I1", "THIRD"),
    R32Fixture(79, "Winner A vs Best 3rd place", "A1", "THIRD"),
    R32Fixture(80, "Winner L vs Best 3rd place", "L1", "THIRD"),
    R32Fixture(81, "Winner D vs Best 3rd place", "D1", "THIRD"),
    R32Fixture(82, "Winner G vs Best 3rd place", "G1", "THIRD"),
    R32Fixture(85, "Winner B vs Best 3rd place", "B1", "THIRD"),
    R32Fixture(87, "Winner K vs Best 3rd place", "K1", "THIRD"),
]

R32_BRACKET: list[R32Fixture] = FIXED_R32_MATCHES + THIRD_PLACE_R32_MATCHES


def assign_third_place_opponents(
    qualifying_thirds: list[tuple[str, str]],  # [(group_letter, team_name), ...], best-ranked first
) -> dict[int, str]:
    """
    Simplified assignment: for each third-place slot (in bracket-slot
    order), assign the best-ranked remaining qualifier whose group does
    NOT match the facing group winner's letter (no immediate rematch).
    Returns {slot_number: team_name}.
    """
    remaining = list(qualifying_thirds)  # (group, team), best-ranked first
    assignment: dict[int, str] = {}

    for fixture in THIRD_PLACE_R32_MATCHES:
        winner_group = fixture.home_rule[0]  # e.g. "E1" -> "E"
        # Find the best-ranked remaining qualifier NOT from winner_group
        chosen_idx = None
        for i, (q_group, _team) in enumerate(remaining):
            if q_group != winner_group:
                chosen_idx = i
                break
        if chosen_idx is None:
            # Extremely rare edge case: only remaining qualifier IS from
            # winner_group. Fall back to allowing it (better than crashing;
            # document as a known edge case).
            chosen_idx = 0

        group, team = remaining.pop(chosen_idx)
        assignment[fixture.slot] = team

    return assignment


def print_summary() -> None:
    print(f"[bracket] {len(FIXED_R32_MATCHES)} fixed matches, "
          f"{len(THIRD_PLACE_R32_MATCHES)} third-place-dependent matches")
    print("\nFixed matches:")
    for fx in FIXED_R32_MATCHES:
        print(f"  Match {fx.slot}: {fx.description}")
    print("\nThird-place-dependent matches (opponent resolved at simulation time):")
    for fx in THIRD_PLACE_R32_MATCHES:
        print(f"  Match {fx.slot}: {fx.description}")


if __name__ == "__main__":
    print_summary()