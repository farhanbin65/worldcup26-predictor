"""
Build the training feature table with strict point-in-time correctness.

Core idea:
1. Reshape matches into one row per (team, match) appearance — a "long" format.
2. For each team, sort by date and compute rolling stats using only PAST rows
   (pandas .shift(1) before .rolling() guarantees today's match is excluded).
3. Merge these as-of features back onto the original home/away match table.
"""

from __future__ import annotations
from pathlib import Path
import pandas as pd

PROCESSED_DIR = Path("data/processed")
REST_DAYS_CAP = 180  # Beyond this, "more rested" carries no extra signal —
                      # a team idle 200+ days isn't meaningfully fresher than
                      # one idle 180 days. Caps prevent rare historical outliers
                      # (pre-1950 sparse fixtures) from distorting feature scale.

def to_long_format(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Turn each match into two rows: one from the home team's perspective,
    one from the away team's. This lets us compute per-team rolling stats
    with a single groupby, instead of juggling home/away separately.
    """
    home_rows = matches.rename(columns={
        "home_team": "team", "away_team": "opponent",
        "home_score": "goals_for", "away_score": "goals_against",
    })
    home_rows["is_home"] = 1

    away_rows = matches.rename(columns={
        "away_team": "team", "home_team": "opponent",
        "away_score": "goals_for", "home_score": "goals_against",
    })
    away_rows["is_home"] = 0

    cols = ["date", "team", "opponent", "goals_for", "goals_against", "is_home"]
    long_df = pd.concat([home_rows[cols], away_rows[cols]], ignore_index=True)

    # win/draw/loss from THIS team's perspective, needed for form/win-rate
    long_df["points"] = 0.0
    long_df.loc[long_df["goals_for"] > long_df["goals_against"], "points"] = 1.0
    long_df.loc[long_df["goals_for"] == long_df["goals_against"], "points"] = 0.5

    long_df = long_df.sort_values(["team", "date"]).reset_index(drop=True)
    return long_df


def add_rolling_form(long_df: pd.DataFrame, windows: list[int] = [5, 10]) -> pd.DataFrame:
    """
    For each team, compute rolling averages over their past N matches.

    THE LEAKAGE-PREVENTION LINE: .shift(1) BEFORE .rolling().
    Without shift(1), row N's rolling window would include row N itself
    (today's match) — that's leakage. shift(1) pushes everything back by
    one row first, so the window for "today" only ever sees matches
    strictly before today.
    """
    long_df = long_df.copy()
    grouped = long_df.groupby("team", group_keys=False)

    for w in windows:
        long_df[f"form_goals_for_{w}"] = grouped["goals_for"].apply(
            lambda s: s.shift(1).rolling(w, min_periods=1).mean()
        )
        long_df[f"form_goals_against_{w}"] = grouped["goals_against"].apply(
            lambda s: s.shift(1).rolling(w, min_periods=1).mean()
        )
        long_df[f"form_points_{w}"] = grouped["points"].apply(
            lambda s: s.shift(1).rolling(w, min_periods=1).mean()
        )

    # Rest days: difference between this match's date and the team's previous one.
    # First match for any team has no previous date -> NaN -> we fill with a
    # neutral default later (median rest, e.g. 60 days) rather than 0, since
    # 0 would wrongly imply "just played yesterday".
    long_df["prev_match_date"] = grouped["date"].shift(1)
    long_df["rest_days"] = (long_df["date"] - long_df["prev_match_date"]).dt.days

    return long_df


def add_head_to_head(matches: pd.DataFrame) -> pd.DataFrame:
    """
    For each match, compute the home team's historical win rate against
    this specific opponent, using only PRIOR meetings.

    Approach: walk through matches chronologically per (team pair), tracking
    a running win/draw/loss tally. We use a frozenset-style sorted pair key
    so 'Brazil vs Argentina' and 'Argentina vs Brazil' share the same history.
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    h2h_record: dict[tuple[str, str], dict[str, int]] = {}

    h2h_home_win_rate = []
    h2h_matches_played = []

    for row in matches.itertuples(index=False):
        pair_key = tuple(sorted([row.home_team, row.away_team]))
        record = h2h_record.get(pair_key, {"home_wins": 0, "draws": 0, "away_wins": 0})
        # NOTE: "home_wins" here means "first-alphabetical-team wins" since the
        # pair key is sorted, not literal home/away. We translate below.
        total = record["home_wins"] + record["draws"] + record["away_wins"]

        if total == 0:
            h2h_home_win_rate.append(0.5)  # no history -> neutral prior
        else:
            first_team_wins = record["home_wins"]
            # Translate back to "current home team's win rate" perspective
            if row.home_team == pair_key[0]:
                rate = (first_team_wins + 0.5 * record["draws"]) / total
            else:
                rate = (record["away_wins"] + 0.5 * record["draws"]) / total
            h2h_home_win_rate.append(rate)

        h2h_matches_played.append(total)

        # NOW update the record with this match's actual result (for future lookups)
        if row.outcome == "H":
            winner_is_first = (row.home_team == pair_key[0])
        elif row.outcome == "A":
            winner_is_first = (row.away_team == pair_key[0])
        else:
            winner_is_first = None  # draw

        record = h2h_record.setdefault(pair_key, {"home_wins": 0, "draws": 0, "away_wins": 0})
        if winner_is_first is None:
            record["draws"] += 1
        elif winner_is_first:
            record["home_wins"] += 1
        else:
            record["away_wins"] += 1

    matches = matches.copy()
    matches["h2h_home_win_rate"] = h2h_home_win_rate
    matches["h2h_matches_played"] = h2h_matches_played
    return matches


def merge_form_onto_matches(matches: pd.DataFrame, long_df: pd.DataFrame) -> pd.DataFrame:
    """Merge the per-team rolling form back onto the home/away match rows."""
    form_cols = [c for c in long_df.columns if c.startswith("form_") or c == "rest_days"]

    home_form = long_df[long_df["is_home"] == 1][["date", "team"] + form_cols].copy()
    home_form.columns = ["date", "home_team"] + [f"home_{c}" for c in form_cols]

    away_form = long_df[long_df["is_home"] == 0][["date", "team"] + form_cols].copy()
    away_form.columns = ["date", "away_team"] + [f"away_{c}" for c in form_cols]

    merged = matches.merge(home_form, on=["date", "home_team"], how="left")
    merged = merged.merge(away_form, on=["date", "away_team"], how="left")
    return merged


def main() -> None:
    matches = pd.read_parquet(PROCESSED_DIR / "matches_with_elo.parquet")
    print(f"[loaded] {len(matches):,} matches with elo")

    long_df = to_long_format(matches)
    long_df = add_rolling_form(long_df)
    print(f"[built] long-format team-appearances: {len(long_df):,} rows")

    matches = merge_form_onto_matches(matches, long_df)
    matches = add_head_to_head(matches)

    # Fill NaNs from first-ever appearances with neutral defaults
    fill_defaults = {
        "home_rest_days": 60, "away_rest_days": 60,
    }
    for col, val in fill_defaults.items():
        if col in matches.columns:
            matches[col] = matches[col].fillna(val)

    # Cap rest_days outliers (see REST_DAYS_CAP comment above)
    for col in ["home_rest_days", "away_rest_days"]:
        n_capped = (matches[col] > REST_DAYS_CAP).sum()
        matches[col] = matches[col].clip(upper=REST_DAYS_CAP)
        print(f"[capped] {col}: {n_capped} rows exceeded {REST_DAYS_CAP} days")

    form_cols = [c for c in matches.columns if "form_" in c]
    matches[form_cols] = matches[form_cols].fillna(matches[form_cols].median(numeric_only=True))

    out = PROCESSED_DIR / "matches_features.parquet"
    matches.to_parquet(out, index=False)
    print(f"[saved] -> {out}")
    print(f"\nColumns ({len(matches.columns)}):")
    print(list(matches.columns))
    print("\nSample row:")
    print(matches.iloc[-1][[
        "date", "home_team", "away_team", "home_score", "away_score",
        "home_elo_pre", "away_elo_pre",
        "home_form_points_5", "away_form_points_5",
        "h2h_home_win_rate", "h2h_matches_played",
    ]])


if __name__ == "__main__":
    main()