# WC2026 Predictor

A machine learning system that predicts FIFA World Cup 2026 match outcomes, simulates the full 48-team tournament 10,000 times via Monte Carlo methods, and serves live predictions through a deployed API and web interface.

**Live site:** https://worldcup26-prediction.vercel.app
**API:** https://worldcup26-predictor.onrender.com

---

## What this project does

Given any two of the 48 World Cup 2026 teams, the system predicts the match outcome (home win / draw / away win) with calibrated probabilities, explains which factors drove that prediction, and — at the tournament level — estimates each team's probability of winning the entire competition based on 10,000 simulated playthroughs of the remaining fixtures, knockout bracket, and group qualification rules.

The project covers the full pipeline: data collection and cleaning, feature engineering with strict leakage prevention, model selection backed by evidence rather than popularity, tournament simulation logic matching FIFA's actual bracket structure, explainability via SHAP, and a deployed full-stack application (FastAPI backend, Next.js frontend).

## Why this isn't just "run XGBoost on football data"

Most student football-prediction projects pick a popular model, get an accuracy number, and stop. This project instead treats every modeling decision as something to justify with evidence:

- **Logistic regression beat a tuned XGBoost classifier** on held-out test data (log loss 0.8622 vs 0.8635), and the reason matters: across six hyperparameter configurations, XGBoost's validation log loss varied by less than 0.002 — noise-level variation, not a real signal that more model complexity helps. This suggested the relationship between Elo, form, and match outcome is close to linear in log-odds space, so the extra nonlinear capacity of gradient boosting had nothing to extract. Logistic regression was kept as the production model for this reason, not because "simpler is always better" as a slogan.

- **Two independent probability calibration methods (isotonic regression and Platt scaling) were tested and both rejected**, because both made the model's Brier score and log loss measurably worse (0.1834 → 0.1851/0.1855) rather than better. The textbook says "calibrate your probabilities" — the evidence here said don't, on this dataset size, and the decision followed the evidence.

- **A genuine data leakage bug was caught and fixed before it reached production**: an early version of the Poisson goals model used one-hot encoded team identity alongside Elo, and L2 regularization silently zeroed out the Elo and home-advantage coefficients entirely (verified: both coefficients were exactly 0.0), because the high-cardinality team encoding absorbed all the signal. The fix was to drop team identity entirely and rely on the same continuous strength features that already worked for the classification model.

## Architecture

```
worldcup26-predictor/
├── backend/
│   ├── api/                  FastAPI app and routers
│   │   ├── main.py
│   │   └── routers/
│   │       ├── fixtures.py       groups, results, remaining fixtures
│   │       ├── standings.py      live group tables with FIFA tiebreakers
│   │       ├── predict.py        on-demand match prediction
│   │       └── tournament.py     precomputed Monte Carlo probabilities
│   ├── src/
│   │   ├── data/              ingestion + Elo rating computation
│   │   ├── features/          feature engineering + EDA
│   │   ├── models/            logistic regression, Poisson, calibration, SHAP
│   │   └── simulation/         tournament structure, group sim, knockout sim, Monte Carlo engine
│   ├── data/processed/        committed parquet files (Elo, features, tournament probabilities)
│   ├── models/                 trained model artifacts (joblib/json)
│   └── requirements.txt
└── frontend/
    └── app/
        ├── page.tsx               results + upcoming fixtures
        ├── standings/page.tsx     live group tables
        ├── predict/page.tsx       interactive match predictor
        └── tournament/page.tsx    championship odds leaderboard
```

Backend deployed on Render (free tier). Frontend deployed on Vercel.

## Data

Match history sourced from [martj42/international_results](https://github.com/martj42/international_results) (MIT-style license, ~49,000 men's international matches since 1872, updated through the live 2026 tournament). The ingestion pipeline (`src/data/ingest.py`) downloads and cleans this directly from GitHub rather than vendoring a static copy, so it always reflects current data.

WC2026 group assignments, results-so-far, and the FIFA-published Round of 32 bracket structure were sourced from ESPN's fixture tracker and Wikipedia's transcription of FIFA's official regulations, and are maintained by hand in `src/simulation/results_so_far.py` as the real tournament progresses — this is a documented limitation, not an oversight, since no reliable structured API exists for in-progress WC2026 fixtures.

## Feature engineering

Every feature is computed **strictly point-in-time**: a feature for a match on date D only uses information available before D. This was tested explicitly — every rolling-window calculation uses `.shift(1)` before `.rolling()`, never after, to guarantee today's match is never accidentally included in its own "recent form" calculation.

Core features:

- **Elo rating**, computed from scratch (not scraped from a ratings site) using a standard chess-Elo-derived formula with three football-specific adjustments: home advantage (+65 points when not a neutral venue), a goal-difference multiplier (margin of victory matters), and a tournament-importance weight (a World Cup match counts roughly 2x a friendly).
- **Recent form** over the last 5 and 10 matches: points won, goals scored, goals conceded.
- **Rest days** since each team's previous match, capped at 180 days — beyond that point, "more rested" carries no additional signal, and the cap prevents rare pre-1950s sparse-fixture outliers from distorting the feature's scale.
- **Head-to-head history**, computed as a running win rate updated chronologically per team pair, with a neutral 0.5 prior for pairs with no prior meetings.

Validation: bucketing matches by Elo difference produces a strictly monotonic home win rate, from 16.3% when massively the underdog to 80.8% when massively the favourite — confirmation that the foundational signal is real before anything was built on top of it.

## Models

| Model | Purpose | Result |
|---|---|---|
| Logistic regression | Match outcome (H/D/A) — **production model** | Log loss 0.8622 (vs. 1.0986 random baseline, 0.9374 Elo-only baseline) |
| XGBoost (tuned) | Outcome — comparison/rejected | Log loss 0.8635, not a meaningful improvement |
| Poisson regression | Expected goals per team → scoreline distribution | Mean Poisson deviance ~22% better than naive average-goals baseline |
| Isotonic / Platt calibration | Probability calibration — tested, rejected | Both increased log loss; uncalibrated model kept |

The Poisson model's derived outcome probabilities (summing the scoreline matrix into win/draw/loss) land within 0.008 log loss of the dedicated classification model — strong convergent validation that two structurally different modeling approaches agree on who is likely to win.

## Tournament simulation

A single simulated tournament: simulate every remaining group match using the trained models, combine with real results into final group tables (FIFA tiebreaker order: points → goal difference → goals scored), determine the 8 best third-place qualifiers, resolve the Round of 32 bracket, then simulate every knockout round through to a champion, with draws resolved via a near-coin-flip penalty shootout model.

**Elo updates dynamically within each simulation** — a team that "wins" its first simulated group match enters its next simulated match with an adjusted rating, exactly mirroring real Elo behaviour. Form, rest days, and head-to-head are frozen at real current values; dynamically simulating rolling 5/10-match windows was judged not worth the added complexity given Elo's dominant feature importance (XGBoost gain: 0.418, more than 3x the next-largest feature).

This was validated by running 200 full tournament simulations and checking the aggregate: a clear favourite like Argentina reached the top 2 in their group 94% of the time, and reached the final in roughly the proportion you'd expect from football intuition — confirming that single unusual-looking outcomes (a strong team finishing 4th once, an underdog reaching the quarterfinal once) were genuine statistical tail events, not bugs, before trusting the model at scale.

The official FIFA "Annex C" lookup table (which exact group's 3rd-place team fills which bracket slot, across 495 possible qualifying combinations) could not be reliably parsed from available sources without risking a silently incorrect mapping. Rather than encode a guessed table and present it as authoritative, this project uses a documented, simpler rule instead: each bracket slot needing a third-place opponent is filled by the best-ranked remaining qualifier whose group doesn't match the facing group winner. The 16 fixed group-winner/runner-up matchups (not dependent on third-place qualification) are taken directly from FIFA's published bracket and are exact.

## Explainability

SHAP values are computed exactly (not approximated) via `shap.LinearExplainer`, since the production model is linear — this has a closed-form relationship to the model's own coefficients, unlike the approximate sampling TreeSHAP needs for ensemble models.

Global SHAP importance, XGBoost's feature importance, and the logistic regression's own coefficients all independently agree: Elo-based features dominate, with `elo_diff` alone carrying roughly 50% more impact than the next-largest feature across all three methods.

A genuine multicollinearity finding: `home_form_points_5` occasionally shows a SHAP contribution in the "wrong" direction for an individual prediction — appearing to suggest good recent form decreases win probability. This was investigated, not dismissed: a direct check of the raw, unconditional relationship between recent form and match outcomes shows a clear, monotonic positive relationship (48.8% → 72.5% win rate across form quartiles). The counter-intuitive sign is a known artifact of `home_form_points_5` correlating with `home_elo_pre` at r=0.577 — both carry real signal about the same underlying thing, and a linear model can mathematically reassign credit between them. The per-match prediction API deliberately excludes form features from its displayed explanation for this reason, surfacing only Elo, head-to-head, and rest-day factors verified to have stable, intuitive directions.

## Known limitations

- Group standings tiebreakers implement points, goal difference, and goals scored, but not disciplinary points or FIFA World Ranking (the 4th/5th official tiebreakers) — these only matter in rare exact ties and were judged not worth the added complexity for a Monte Carlo simulation run thousands of times.
- The Round of 32 third-place assignment uses a documented simplified rule rather than FIFA's exact 495-combination official table (see Tournament Simulation above).
- `results_so_far.py` requires manual updates as the real tournament progresses; the Monte Carlo batch (`src/simulation/monte_carlo.py`) must be re-run periodically to keep `tournament_probabilities.json` current.
- The deployed API excludes SHAP from the live `/predict/match` endpoint. SHAP's import cost (effectively bundled with scikit-learn/pandas at ~219MB, since `shap` eagerly imports both) pushed total memory close to Render's free-tier ceiling; SHAP explanations remain fully available offline (`src/models/shap_explain.py`, `src/models/shap_global.py`) and are summarized above, but the live endpoint returns probabilities and the dominant Elo-based factor without a full SHAP breakdown.

## Running locally

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Tech stack

**ML / data:** Python, pandas, scikit-learn, SciPy (Poisson), SHAP
**Backend:** FastAPI, deployed on Render
**Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, deployed on Vercel
**Data source:** [martj42/international_results](https://github.com/martj42/international_results)