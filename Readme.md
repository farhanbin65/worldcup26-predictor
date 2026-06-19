# WC2026 Predictor

![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)
![Deployed on Vercel](https://img.shields.io/badge/Frontend-Vercel-black?style=flat-square&logo=vercel)
![API on Render](https://img.shields.io/badge/API-Render-46E3B7?style=flat-square&logo=render&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-00c97a?style=flat-square)

A full-stack FIFA World Cup 2026 prediction engine. Calibrated match outcome probabilities, live group standings, and a 10,000-run Monte Carlo tournament simulation served through a FastAPI backend and a Next.js frontend.

**Live site:** https://worldcup26-prediction.vercel.app  


> The API runs on Render's free tier and sleeps after 15 minutes of inactivity. The first request after sleep takes approximately 30 seconds. Visit the /docs endpoint to wake the instance before using the site.

---

## What this project does

Given any two of the 48 World Cup 2026 teams, the system predicts the match outcome (home win / draw / away win) with calibrated probabilities and explains which factors drove that prediction. At the tournament level, it estimates each team's probability of winning the competition and reaching each knockout round, based on 10,000 simulated playthroughs of the full bracket.

The frontend exposes four pages:

| Page | Description |
|---|---|
| Results | Live group stage results and upcoming fixtures, with a predicted champion card pulled from the Monte Carlo simulation |
| Standings | Live group tables with FIFA tiebreaker logic and qualification indicators per team |
| Predict | Pick any two teams and get calibrated win, draw, and loss probabilities with animated bars and a winner verdict |
| Tournament | Split knockout bracket populated with Monte Carlo top contenders, plus a ranked championship odds leaderboard |

---

## Why this is not just "run XGBoost on football data"

Most student football-prediction projects pick a popular model, get an accuracy number, and stop. This project treats every modeling decision as something to justify with evidence.

**Logistic regression beat tuned XGBoost (log loss 0.8622 vs 0.8635)**

Across six hyperparameter configurations, XGBoost's validation log loss varied by less than 0.002, which is noise-level variation rather than a real signal that more model complexity helps. The relationship between Elo, form, and match outcome is close to linear in log-odds space, so gradient boosting had nothing extra to extract. Logistic regression was kept as the production model for this reason, not because simpler is always better as a slogan.

**Two calibration methods tested and both rejected**

Isotonic regression and Platt scaling both made the model's Brier score and log loss measurably worse (0.1834 to 0.1851 and 0.1855 respectively). The textbook says to calibrate your probabilities. The evidence on this dataset said not to, and the decision followed the evidence.

**A genuine data leakage bug was caught and fixed before production**

An early version of the Poisson goals model used one-hot encoded team identity alongside Elo. L2 regularization silently zeroed out both the Elo and home-advantage coefficients (verified: exactly 0.0) because the high-cardinality team encoding absorbed all the signal. The fix was to drop team identity entirely and rely on the continuous strength features that already worked for the classification model.

---


## Models

| Model | Purpose | Result |
|---|---|---|
| Logistic regression | Match outcome (H/D/A) — production model | Log loss 0.8622 vs 1.0986 random baseline and 0.9374 Elo-only baseline |
| XGBoost (tuned, 6 configs) | Outcome comparison — rejected | Log loss 0.8635, not a meaningful improvement over logistic regression |
| Poisson regression | Expected goals per team, scoreline distribution | Mean Poisson deviance approximately 22% better than naive average-goals baseline |
| Isotonic calibration | Probability calibration — tested, rejected | Increased log loss from 0.1834 to 0.1851 |
| Platt scaling | Probability calibration — tested, rejected | Increased log loss from 0.1834 to 0.1855 |

The Poisson model's derived outcome probabilities land within 0.008 log loss of the dedicated classification model, which is strong convergent validation that two structurally different approaches agree on who is likely to win.

---

## Feature engineering

Every feature is computed strictly point-in-time. A feature for a match on date D only uses information available before D. All rolling-window calculations use `.shift(1)` before `.rolling()`, never after.

| Feature | Description |
|---|---|
| Elo rating | Computed from scratch with home advantage (+65 pts), goal-difference multiplier, and tournament-importance weight (World Cup match counts approximately 2x a friendly) |
| Recent form (5 and 10 matches) | Points won, goals scored, goals conceded over the last 5 and 10 matches |
| Rest days | Days since each team's previous match, capped at 180 (beyond that point, more rest carries no additional signal) |
| Head-to-head history | Running win rate per team pair, updated chronologically, with a neutral 0.5 prior for pairs with no prior meetings |

Validation: bucketing matches by Elo difference produces a strictly monotonic home win rate, from 16.3% when massively the underdog to 80.8% when massively the favourite.

---

## Tournament simulation

A single simulated tournament works as follows: simulate every remaining group match using the trained model, combine with real results into final group tables using FIFA tiebreaker order (points, then goal difference, then goals scored), determine the 8 best third-place qualifiers, resolve the Round of 32 bracket, then simulate every knockout round through to a champion.

Elo updates dynamically within each simulation. A team that wins its first simulated group match enters its next match with an adjusted rating, mirroring real Elo behaviour.

10,000 simulations are run in batch via `src/simulation/monte_carlo.py` and results stored in `tournament_probabilities.json`. The tournament page reads this precomputed file rather than running simulations on request.

The Round of 32 third-place assignment uses a documented simplified rule rather than FIFA's exact 495-combination official table. The 16 fixed group-winner and runner-up matchups are taken directly from FIFA's published bracket.

---

## Explainability

SHAP values are computed exactly (not approximated) via `shap.LinearExplainer`, since the production model is linear. Global SHAP importance, XGBoost's feature importance, and the logistic regression's own coefficients all independently agree: `elo_diff` alone carries roughly 50% more impact than the next-largest feature across all three methods.

`home_form_points_5` occasionally shows a SHAP contribution in the wrong direction for individual predictions. This was investigated rather than dismissed. A direct check of the raw relationship between recent form and match outcomes shows a clear monotonic positive relationship (48.8% to 72.5% win rate across form quartiles). The counter-intuitive sign is a known artifact of `home_form_points_5` correlating with `home_elo_pre` at r=0.577. The per-match prediction API excludes form features from its displayed explanation for this reason.

SHAP is excluded from the live `/predict/match` endpoint. Its import cost (bundled with scikit-learn and pandas at approximately 219MB) pushed total memory close to Render's free-tier ceiling. SHAP explanations remain fully available offline via `src/models/shap_explain.py` and `src/models/shap_global.py`.

---

## Frontend

**Stack:** Next.js 15 (App Router), TypeScript, Tailwind CSS v4, deployed on Vercel

**Design system:** Dark quant-tool aesthetic. Base color `#0d1a14`, accent `#00c97a` (pitch green), IBM Plex Mono for all data and numbers, Inter for body text. Subtle pitch-grid CSS pattern on the body background. All colors defined as CSS custom properties in `globals.css`.

**Key implementation decisions:**

- Server Components for all data-fetching pages (`/` and `/standings`). No client-side loading states, no layout shift on load.
- `"use client"` used only where interactivity is required (`/predict` and the `/tournament` tab switcher).
- Hover effects handled entirely in CSS. No `onMouseEnter` or `onMouseLeave` in Server Components, which would throw a runtime error in Next.js App Router.
- Flag images from [flagicons.lipis.dev](https://flagicons.lipis.dev) (SVG, 4:3 ratio, ISO 3166-1 alpha-2 codes).
- Backend warming banner with a direct link to Render `/docs` to wake the free-tier instance before use.

---

## Data

Match history sourced from [martj42/international_results](https://github.com/martj42/international_results) (MIT-style license, approximately 49,000 men's international matches since 1872, updated through the live 2026 tournament). The ingestion pipeline downloads directly from GitHub rather than vendoring a static copy.

WC2026 group assignments, results, and the FIFA-published Round of 32 bracket are maintained by hand in `src/simulation/results_so_far.py` as the real tournament progresses. This is a documented limitation rather than an oversight, since no reliable structured API exists for in-progress WC2026 fixtures.

---

## Known limitations

- Group standings tiebreakers implement points, goal difference, and goals scored, but not disciplinary points or FIFA World Ranking (the 4th and 5th official tiebreakers).
- The Round of 32 third-place assignment uses a simplified rule rather than FIFA's exact 495-combination official table.
- `results_so_far.py` requires manual updates as the tournament progresses. `monte_carlo.py` must be re-run periodically to keep `tournament_probabilities.json` current.
- SHAP is excluded from the live prediction endpoint due to Render free-tier memory constraints.

---

## Tech stack

| Layer | Technology |
|---|---|
| ML and data | Python, pandas, scikit-learn, SciPy (Poisson), SHAP |
| Backend | FastAPI, Uvicorn, Render |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, Vercel |
| Data source | martj42/international_results |
| Flag images | flagicons.lipis.dev |

---

## Author

Built by [@farhanbin65](https://github.com/farhanbin65)  
Portfolio: [farhanbin.dev](https://farhanbin.dev)