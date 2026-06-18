// app/predict/page.tsx
"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface PredictionResult {
  home_team: string;
  away_team: string;
  home_elo: number;
  away_elo: number;
  probabilities: { [outcome: string]: number };
  predicted_outcome: string;
  summary: string;
}

export default function PredictPage() {
  const [teams, setTeams] = useState<string[]>([]);
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch the valid team list once, when the page first loads
  useEffect(() => {
    fetch(`${API_URL}/predict/teams`)
      .then((res) => res.json())
      .then((data) => setTeams(data.teams))
      .catch(() => setError("Could not load team list."));
  }, []);

  async function handlePredict() {
    if (!homeTeam || !awayTeam) {
      setError("Please select both teams.");
      return;
    }
    if (homeTeam === awayTeam) {
      setError("Home and away teams must be different.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/predict/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam }),
      });
      const data = await res.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResult(data);
      }
    } catch {
      setError("Prediction request failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Predict a Match</h1>

      <div className="flex gap-4 items-end mb-6">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Home team</label>
          <select
            value={homeTeam}
            onChange={(e) => setHomeTeam(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
          >
            <option value="">Select team</option>
            {teams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1">Away team</label>
          <select
            value={awayTeam}
            onChange={(e) => setAwayTeam(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
          >
            <option value="">Select team</option>
            {teams.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <button
          onClick={handlePredict}
          disabled={loading}
          className="bg-white text-black px-4 py-2 rounded font-medium disabled:opacity-50"
        >
          {loading ? "Predicting..." : "Predict"}
        </button>
      </div>

      {error && <p className="text-red-400 mb-4">{error}</p>}

      {result && (
        <div className="border border-gray-700 rounded p-6 max-w-md">
          <h2 className="text-xl font-semibold mb-2">
            {result.home_team} vs {result.away_team}
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            Elo: {result.home_elo} vs {result.away_elo}
          </p>

          <div className="space-y-2 mb-4">
            {Object.entries(result.probabilities).map(([outcome, pct]) => (
              <div key={outcome} className="flex justify-between">
                <span>{outcome}</span>
                <span className="font-mono">{pct}%</span>
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-300">{result.summary}</p>
        </div>
      )}
    </main>
  );
}