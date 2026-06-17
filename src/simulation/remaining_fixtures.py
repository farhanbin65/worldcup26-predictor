"""
WC2026 remaining group stage fixtures (not yet played), with real dates.

Source: ESPN fixtures page. Static once published — group stage schedule
is fixed by FIFA, unlike results which need manual updates.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Fixture:
    date: str
    group: str
    home: str
    away: str


REMAINING_FIXTURES: list[Fixture] = [
    # June 16 (may already be played by the time you run this — check
    # results_so_far.py and avoid double-counting once you add them there)
    Fixture("2026-06-16", "I", "France", "Senegal"),
    Fixture("2026-06-16", "I", "Iraq", "Norway"),
    Fixture("2026-06-16", "J", "Argentina", "Algeria"),
    Fixture("2026-06-16", "J", "Austria", "Jordan"),

    # June 17
    Fixture("2026-06-17", "K", "Portugal", "DR Congo"),
    Fixture("2026-06-17", "L", "England", "Croatia"),
    Fixture("2026-06-17", "L", "Ghana", "Panama"),
    Fixture("2026-06-17", "K", "Uzbekistan", "Colombia"),

    # June 18
    Fixture("2026-06-18", "A", "Czechia", "South Africa"),
    Fixture("2026-06-18", "B", "Switzerland", "Bosnia and Herzegovina"),
    Fixture("2026-06-18", "B", "Canada", "Qatar"),
    Fixture("2026-06-18", "A", "Mexico", "South Korea"),

    # June 19
    Fixture("2026-06-19", "D", "United States", "Australia"),
    Fixture("2026-06-19", "C", "Scotland", "Morocco"),
    Fixture("2026-06-19", "C", "Brazil", "Haiti"),
    Fixture("2026-06-19", "D", "Turkiye", "Paraguay"),

    # June 20
    Fixture("2026-06-20", "F", "Netherlands", "Sweden"),
    Fixture("2026-06-20", "E", "Germany", "Ivory Coast"),
    Fixture("2026-06-20", "E", "Ecuador", "Curacao"),
    Fixture("2026-06-20", "F", "Tunisia", "Japan"),

    # June 21
    Fixture("2026-06-21", "H", "Spain", "Saudi Arabia"),
    Fixture("2026-06-21", "G", "Belgium", "Iran"),
    Fixture("2026-06-21", "H", "Uruguay", "Cape Verde"),
    Fixture("2026-06-21", "G", "New Zealand", "Egypt"),

    # June 22
    Fixture("2026-06-22", "J", "Argentina", "Austria"),
    Fixture("2026-06-22", "I", "France", "Iraq"),
    Fixture("2026-06-22", "I", "Norway", "Senegal"),
    Fixture("2026-06-22", "J", "Jordan", "Algeria"),

    # June 23
    Fixture("2026-06-23", "K", "Portugal", "Uzbekistan"),
    Fixture("2026-06-23", "L", "England", "Ghana"),
    Fixture("2026-06-23", "L", "Panama", "Croatia"),
    Fixture("2026-06-23", "K", "Colombia", "DR Congo"),

    # June 24
    Fixture("2026-06-24", "B", "Switzerland", "Canada"),
    Fixture("2026-06-24", "B", "Bosnia and Herzegovina", "Qatar"),
    Fixture("2026-06-24", "C", "Scotland", "Brazil"),
    Fixture("2026-06-24", "C", "Morocco", "Haiti"),
    Fixture("2026-06-24", "A", "Czechia", "Mexico"),
    Fixture("2026-06-24", "A", "South Africa", "South Korea"),

    # June 25
    Fixture("2026-06-25", "E", "Ecuador", "Germany"),
    Fixture("2026-06-25", "E", "Curacao", "Ivory Coast"),
    Fixture("2026-06-25", "F", "Japan", "Sweden"),
    Fixture("2026-06-25", "F", "Tunisia", "Netherlands"),
    Fixture("2026-06-25", "D", "Turkiye", "United States"),
    Fixture("2026-06-25", "D", "Paraguay", "Australia"),

    # June 26
    Fixture("2026-06-26", "I", "Norway", "France"),
    Fixture("2026-06-26", "I", "Senegal", "Iraq"),
    Fixture("2026-06-26", "H", "Cape Verde", "Saudi Arabia"),
    Fixture("2026-06-26", "H", "Uruguay", "Spain"),
    Fixture("2026-06-26", "G", "Egypt", "Iran"),
    Fixture("2026-06-26", "G", "New Zealand", "Belgium"),

    # June 27
    Fixture("2026-06-27", "L", "Panama", "England"),
    Fixture("2026-06-27", "L", "Croatia", "Ghana"),
    Fixture("2026-06-27", "K", "Colombia", "Portugal"),
    Fixture("2026-06-27", "K", "DR Congo", "Uzbekistan"),
    Fixture("2026-06-27", "J", "Algeria", "Austria"),
    Fixture("2026-06-27", "J", "Jordan", "Argentina"),
]


def print_summary() -> None:
    print(f"[fixtures] {len(REMAINING_FIXTURES)} remaining group matches")


if __name__ == "__main__":
    print_summary()