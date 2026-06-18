"""
Fixtures and results endpoints.

Serves the static group structure + real results-so-far + remaining
fixtures, all already built and verified in Phase 8. No model inference
here — pure data serving, which is why it's the simplest endpoint to wire
up first.
"""

from __future__ import annotations
from fastapi import APIRouter

from src.simulation.tournament_structure import GROUPS
from src.simulation.results_so_far import RESULTS_SO_FAR
from src.simulation.remaining_fixtures import REMAINING_FIXTURES

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.get("/groups")
def get_groups():
    """Returns the 12 groups and their 4 teams each."""
    return {"groups": GROUPS}


@router.get("/results")
def get_results():
    """Returns all real match results recorded so far."""
    return {
        "count": len(RESULTS_SO_FAR),
        "results": [
            {
                "date": r.date, "group": r.group,
                "home": r.home, "away": r.away,
                "home_score": r.home_score, "away_score": r.away_score,
            }
            for r in RESULTS_SO_FAR
        ],
    }


@router.get("/remaining")
def get_remaining_fixtures():
    """Returns all group-stage matches not yet played."""
    return {
        "count": len(REMAINING_FIXTURES),
        "fixtures": [
            {"date": f.date, "group": f.group, "home": f.home, "away": f.away}
            for f in REMAINING_FIXTURES
        ],
    }