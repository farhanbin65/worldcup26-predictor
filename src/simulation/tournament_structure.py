"""
WC2026 tournament structure: groups, fixtures, and constants.

This is STATIC data (group assignments don't change once announced) —
separate from LIVE data (match results so far), which we'll fetch and
update separately in the next script. Keeping these separate means we
can refresh live results without ever touching this file.
"""

from __future__ import annotations

GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "South Korea", "Czechia", "South Africa"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Australia", "Paraguay", "Turkiye"],
    "E": ["Germany", "Ivory Coast", "Ecuador", "Curacao"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Uruguay", "Saudi Arabia", "Cape Verde"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Austria", "Algeria", "Jordan"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "DR Congo"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

NAME_ALIASES: dict[str, str] = {
    "Czechia": "Czech Republic",
    "Turkiye": "Turkey",
    "Curacao": "Curaçao",
}

def to_dataset_name(team: str) -> str:
    """Translate a GROUPS-style team name to its historical dataset name."""
    return NAME_ALIASES.get(team, team)

# IMPORTANT: team names here must EXACTLY match names used in
# martj42/international_results, since that's what our Elo/form lookups
# key on. We'll verify this with a name-matching check before simulating —
# mismatches (e.g. "Ivory Coast" vs "Côte d'Ivoire", "Turkiye" vs "Turkey",
# "USA" vs "United States") are a classic silent-failure source.

ALL_TEAMS = [team for group in GROUPS.values() for team in group]

assert len(ALL_TEAMS) == 48, f"Expected 48 teams, got {len(ALL_TEAMS)}"
assert len(set(ALL_TEAMS)) == 48, "Duplicate team name found across groups!"

TOURNAMENT_NAME = "FIFA World Cup"  # must match the `tournament` column
                                     # value used in elo.py's TOURNAMENT_WEIGHTS

GROUP_STAGE_START = "2026-06-11"
GROUP_STAGE_END = "2026-06-27"


def print_summary() -> None:
    print(f"[structure] {len(GROUPS)} groups, {len(ALL_TEAMS)} teams total")
    for letter, teams in GROUPS.items():
        print(f"  Group {letter}: {', '.join(teams)}")


def validate_against_dataset(known_teams: set[str]) -> None:
    """Confirm every team (after alias translation) exists in the historical dataset."""
    missing = []
    for team in ALL_TEAMS:
        dataset_name = to_dataset_name(team)
        if dataset_name not in known_teams:
            missing.append((team, dataset_name))

    if missing:
        print(f"\n[WARNING] {len(missing)} teams still unmatched after aliasing:")
        for original, attempted in missing:
            print(f"  {original} -> tried '{attempted}', not found")
    else:
        print(f"\n[validated] All {len(ALL_TEAMS)} teams resolve correctly after aliasing.")


if __name__ == "__main__":
    print_summary()

    import pandas as pd
    df = pd.read_parquet("data/processed/elo_current.parquet")
    validate_against_dataset(set(df["team"]))