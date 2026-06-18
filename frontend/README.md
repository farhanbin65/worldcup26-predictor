# WC2026 Predictor

![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Vercel](https://img.shields.io/badge/Deployed-Vercel-black?style=flat-square&logo=vercel)
![Render](https://img.shields.io/badge/API-Render-46E3B7?style=flat-square&logo=render&logoColor=black)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-00c97a?style=flat-square)

A full-stack FIFA World Cup 2026 prediction engine — calibrated match predictions, live group standings, and a 10,000-run Monte Carlo tournament simulation, served through a FastAPI backend and a Next.js frontend.

**Live site:** https://worldcup26-prediction.vercel.app  
**API:** https://worldcup26-predictor.onrender.com  
**API docs:** https://worldcup26-predictor.onrender.com/docs

> **Note:** The API runs on Render's free tier and sleeps after 15 minutes of inactivity. First request after sleep takes ~30s. Hit the [/docs](https://worldcup26-predictor.onrender.com/docs) endpoint to wake it before visiting the site.

---

## What this project does

Given any two of the 48 World Cup 2026 teams, the system predicts the match outcome (home win / draw / away win) with calibrated probabilities and explains which factors drove that prediction. At the tournament level, it estimates each team's probability of winning the entire competition — and reaching each knockout round — based on 10,000 simulated playthroughs of the full bracket.

The frontend exposes four views:

| Page | Description |
|---|---|
| **Results** | Live group stage results and upcoming fixtures, with a predicted champion card pulled from the Monte Carlo simulation |
| **Standings** | Live group tables with FIFA tiebreaker logic, qualification indicators per team |
| **Predict** | Pick any two teams, get calibrated win/draw/loss probabilities with animated bars and a winner verdict |
| **Tournament** | Split knockout bracket populated with Monte Carlo top contenders + ranked championship odds leaderboard |

---

## Why this isn't just "run XGBoost on football data"

Most student football-prediction projects pick a popular model, get an accuracy number, and stop. This project treats every modeling decision as something to justify with evidence:

**Logistic regression beat tuned XGBoost (log loss 0.8622 vs 0.8635)**  
Across six hyperparameter configurations, XGBoost's validation log loss varied by less than 0.002 — noise-level variation, not a real signal that more model complexity helps. The relationship between Elo, form, and match outcome is close to linear in log-odds space, so gradient boosting had nothing extra to extract. Logistic regression was kept as the production model for this reason, not because "simpler is always better" as a slogan.

**Two calibration methods tested and both rejected**  
Isotonic regression and Platt scaling both made the model's Brier score and log loss measurably worse (0.1834 → 0.1851/0.1855). The textbook says "calibrate your probabilities" — the evidence here said don't, on this dataset size, and the decision followed the evidence.

**A genuine data leakage bug was caught and fixed before production**  
An early version of the Poisson goals model used one-hot encoded team identity alongside Elo, and L2 regularization silently zeroed out both the Elo and home-advantage coefficients (verified: exactly 0.0), because the high-cardinality team encoding absorbed all the signal. Fix: drop team identity entirely and rely on the continuous strength features that already worked for the classification model.

---

## Architecture

```
worldcup26-predictor/
├── backend/
│   ├── api/
│   │   ├── main.py
│   │   └── routers/
│   │       ├── fixtures.py        group results + remaining fixtures
│   │       ├── standings.py       live group tables with FIFA tiebreakers
│   │       ├── predict.py         on-demand match prediction
│   │       └── tournament.py      precomputed Monte Carlo probabilities
│   ├── src/
│   │   ├── data/                  ingestion + Elo rating computation
│   │   ├── features/              feature engineering + EDA
│   │   ├── models/                logistic regression, Poisson, calibration, SHAP
│   │   └── simulation/            tournament structure, group sim, knockout sim, Monte Carlo
│   ├── data/processed/            parquet files (Elo, features, tournament probabilities)
│   ├── models/                    trained model artifacts (joblib/json)
│   └── requirements.txt
└── frontend/
    └── app/
        ├── page.tsx               results + upcoming fixtures + predicted champion card
        ├── standings/page.tsx     live group tables
        ├── predict/page.tsx       interactive match predictor with VS layout
        ├── tournament/page.tsx    knockout bracket + championship odds leaderboard
        ├── layout.tsx             shared nav + font wiring
        └── globals.css            design tokens + pitch-grid background
```

---

## Models

| Model | Purpose | Result |
|---|---|---|
| Logistic regression | Match outcome (H/D/A) — **production model** | Log loss **0.8622** (vs 1.0986 random, 0.9374 Elo-only baseline) |
| XGBoost (tuned) | Outcome — comparison / rejected | Log loss 0.8635, not a meaningful improvement |
| Poisson regression | Expected goals per team → scoreline distribution | Mean Poisson deviance ~22% better than naive average-goals baseline |
| Isotonic / Platt calibration | Probability calibration — tested, rejected | Both increased log loss; uncalibrated model kept |

---

## Feature engineering

Every feature is computed **strictly point-in-time**: a feature for a match on date D only uses information available before D. Rolling-window calculations use `.shift(1)` before `.rolling()`, never after.

| Feature | Description |
|---|---|
| **Elo rating** | Computed from scratch — home advantage (+65pts), goal-difference multiplier, tournament-importance weight (WC ≈ 2× friendly) |
| **Recent form** | Points won, goals scored, goals conceded over last 5 and 10 matches |
| **Rest days** | Days since each team's previous match, capped at 180 |
| **Head-to-head** | Running win rate per team pair, chronologically updated, 0.5 prior for new pairs |

Validation: bucketing matches by Elo difference produces a strictly monotonic home win rate (16.3% when massively the underdog → 80.8% when massively the favourite).

---

## Tournament simulation

A single simulated tournament: simulate every remaining group match using the trained model, combine with real results into final group tables (FIFA tiebreaker order: points → goal difference → goals scored), determine the 8 best third-place qualifiers, resolve the Round of 32 bracket, then simulate every knockout round through to a champion.

**Elo updates dynamically within each simulation** — a team that wins its first simulated group match enters its next match with an adjusted rating, mirroring real Elo behaviour.

10,000 simulations are run in batch (`src/simulation/monte_carlo.py`) and results stored in `tournament_probabilities.json`. The tournament page reads this precomputed file rather than running simulations on request.

---

## Explainability

SHAP values are computed exactly (not approximated) via `shap.LinearExplainer`, since the production model is linear. Global SHAP importance, XGBoost's feature importance, and logistic regression's own coefficients all independently agree: `elo_diff` alone carries roughly 50% more impact than the next-largest feature.

A multicollinearity finding: `home_form_points_5` occasionally shows a SHAP contribution in the "wrong" direction for individual predictions — a known artifact of it correlating with `home_elo_pre` at r=0.577. The per-match prediction API deliberately excludes form features from its displayed explanation, surfacing only Elo, head-to-head, and rest-day factors verified to have stable, intuitive directions.

> SHAP is excluded from the live `/predict/match` endpoint. SHAP's import cost (~219MB bundled with scikit-learn/pandas) pushed total memory close to Render's free-tier ceiling. SHAP explanations remain fully available offline (`src/models/shap_explain.py`, `src/models/shap_global.py`).

---

## Frontend

![Dark quant dashboard screenshot](https://worldcup26-prediction.vercel.app/og.png)

**Stack:** Next.js 15 (App Router) · TypeScript · Tailwind CSS v4 · Vercel

**Design:** Dark quant-tool aesthetic — `#0d1a14` base, `#00c97a` pitch-green accent, IBM Plex Mono for all data and numbers, Inter for body. Subtle pitch-grid CSS pattern on the body background. All colors defined as CSS custom properties.

**Architecture decisions:**
- Server Components for all data-fetching pages (`/`, `/standings`) — no client-side loading states, no layout shift
- `"use client"` only where interactivity is required (`/predict`, `/tournament` tab switcher)
- Hover effects handled entirely in CSS — no `onMouseEnter`/`onMouseLeave` in Server Components
- Flag images from [flagicons.lipis.dev](https://flagicons.lipis.dev) (SVG, 4:3, ISO 3166-1 alpha-2)
- Backend warming banner with direct link to Render `/docs` to wake the free-tier instance

---

## Data

Match history from [martj42/international_results](https://github.com/martj42/international_results) (MIT-style license, ~49,000 men's international matches since 1872, updated through the live 2026 tournament). Ingested directly from GitHub rather than vendoring a static copy.

WC2026 group assignments, results, and the FIFA-published Round of 32 bracket are maintained by hand in `src/simulation/results_so_far.py` as the real tournament progresses — documented limitation, not an oversight, since no reliable structured API exists for in-progress WC2026 fixtures.

---

## Known limitations

- Group standings tiebreakers implement points, goal difference, and goals scored — not disciplinary points or FIFA World Ranking (4th/5th official tiebreakers)
- The Round of 32 third-place assignment uses a documented simplified rule rather than FIFA's exact 495-combination official table
- `results_so_far.py` requires manual updates as the real tournament progresses; `monte_carlo.py` must be re-run periodically to keep `tournament_probabilities.json` current
- SHAP excluded from the live prediction endpoint due to Render free-tier memory constraints

---

## Running locally

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows
# source .venv/bin/activate     # macOS/Linux
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

---

## Tech stack

| Layer | Technology |
|---|---|
| ML / data | Python, pandas, scikit-learn, SciPy (Poisson), SHAP |
| Backend | FastAPI, Uvicorn, deployed on Render |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, deployed on Vercel |
| Data source | [martj42/international_results](https://github.com/martj42/international_results) |
| Flags | [flagicons.lipis.dev](https://flagicons.lipis.dev) |

---

## Author

Built by [@farhanbin65](https://github.com/farhanbin65) · Portfolio at [farhanbin.dev](https://farhanbin.dev)