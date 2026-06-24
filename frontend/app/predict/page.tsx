"use client";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface PredictionResult {
  home_team: string; away_team: string;
  home_elo: number; away_elo: number;
  probabilities: { [outcome: string]: number };
  predicted_outcome: string; summary: string;
}

const TEAM_CODE: Record<string, string> = {
  "Spain": "es", "France": "fr", "Argentina": "ar", "England": "gb-eng",
  "Brazil": "br", "Portugal": "pt", "Germany": "de", "Netherlands": "nl",
  "Belgium": "be", "Italy": "it", "Croatia": "hr", "Uruguay": "uy",
  "Colombia": "co", "Morocco": "ma", "Japan": "jp", "USA": "us",
  "United States": "us", "Mexico": "mx", "Norway": "no", "Canada": "ca",
  "Turkey": "tr", "Turkiye": "tr", "Serbia": "rs", "Denmark": "dk",
  "Switzerland": "ch", "Sweden": "se", "Scotland": "gb-sct", "Wales": "gb-wls",
  "Australia": "au", "South Korea": "kr", "Ecuador": "ec", "Senegal": "sn",
  "Iran": "ir", "Qatar": "qa", "Saudi Arabia": "sa", "Ghana": "gh",
  "Tunisia": "tn", "Cameroon": "cm", "Nigeria": "ng", "Algeria": "dz",
  "Egypt": "eg", "Ukraine": "ua", "Austria": "at", "Poland": "pl",
  "Paraguay": "py", "Chile": "cl", "Costa Rica": "cr", "Panama": "pa",
  "Ivory Coast": "ci", "Bolivia": "bo", "Venezuela": "ve", "Peru": "pe",
  "Czechia": "cz", "Slovakia": "sk", "Romania": "ro", "Hungary": "hu",
  "Bosnia and Herzegovina": "ba", "Iceland": "is", "Finland": "fi",
  "South Africa": "za", "New Zealand": "nz", "Haiti": "ht", "Curacao": "cw",
  "Jamaica": "jm", "Honduras": "hn", "El Salvador": "sv", "Guatemala": "gt",
  "DR Congo": "cd", "Mali": "ml", "Iraq": "iq", "UAE": "ae",
  "Jordan": "jo", "Uzbekistan": "uz", "Kazakhstan": "kz", "China": "cn",
  "Thailand": "th", "Vietnam": "vn", "Indonesia": "id", "Philippines": "ph",
};

function Flag({ team, size = 32 }: { team: string; size?: number }) {
  const code = TEAM_CODE[team];
  if (!code) return (
    <div style={{
      width: size * 1.33, height: size,
      background: "var(--border)", borderRadius: "4px", flexShrink: 0,
    }} />
  );
  return (
    <img
      src={`https://flagicons.lipis.dev/flags/4x3/${code}.svg`}
      alt={team}
      width={Math.round(size * 1.33)}
      height={size}
      style={{ borderRadius: "4px", objectFit: "cover", flexShrink: 0, display: "block" }}
    />
  );
}

function TeamPicker({
  label, value, teams, onChange,
}: {
  label: string; value: string; teams: string[]; onChange: (v: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px", flex: 1, minWidth: 0 }}>
      <span style={{
        fontFamily: "var(--font-mono)", fontSize: "10px",
        color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase",
        whiteSpace: "nowrap",
      }}>{label}</span>

      <div style={{
        width: "100%", maxWidth: "120px", aspectRatio: "4/3",
        border: "1px solid var(--border)", borderRadius: "10px",
        overflow: "hidden", background: "var(--bg)",
        display: "flex", alignItems: "center", justifyContent: "center",
        transition: "border-color 0.2s",
        borderColor: value ? "var(--accent-dim)" : "var(--border)",
      }}>
        {value ? (
          <img
            src={`https://flagicons.lipis.dev/flags/4x3/${TEAM_CODE[value] ?? "un"}.svg`}
            alt={value}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)" }}>?</span>
        )}
      </div>

      <div style={{
        fontFamily: "var(--font-mono)", fontSize: "13px",
        color: value ? "var(--text)" : "var(--text-faint)",
        fontWeight: value ? 500 : 400, minHeight: "18px", textAlign: "center",
        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        maxWidth: "100%",
      }}>
        {value || "—"}
      </div>

      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
          background: "var(--bg)", border: "1px solid var(--border)",
          color: "var(--text-dim)", fontSize: "11px", padding: "7px 8px",
          borderRadius: "8px", width: "100%", maxWidth: "150px",
          fontFamily: "var(--font-mono)", outline: "none", cursor: "pointer",
          boxSizing: "border-box",
        }}
      >
        <option value="">Select team</option>
        {teams.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
    </div>
  );
}

function ProbBar({
  label, pct, color, delay = 0,
}: {
  label: string; pct: number; color: string; delay?: number;
}) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 100 + delay);
    return () => clearTimeout(t);
  }, [pct, delay]);

  return (
    <div style={{ marginBottom: "14px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "6px" }}>
        <span style={{ fontSize: "13px", color: "var(--text-dim)", textTransform: "capitalize" }}>{label}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "16px", fontWeight: 500, color }}>{pct}%</span>
      </div>
      <div style={{ height: "6px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
        <div style={{
          height: "100%", borderRadius: "3px",
          background: color,
          width: `${width}%`,
          transition: "width 0.7s cubic-bezier(0.4,0,0.2,1)",
        }} />
      </div>
    </div>
  );
}

export default function PredictPage() {
  const [teams, setTeams] = useState<string[]>([]);
  const [homeTeam, setHomeTeam] = useState("");
  const [awayTeam, setAwayTeam] = useState("");
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/predict/teams`)
      .then(r => r.json())
      .then(d => setTeams(d.teams ?? []))
      .catch(() => setError("Could not load team list."));
  }, []);

  async function handlePredict() {
    if (!homeTeam || !awayTeam) { setError("Select both teams."); return; }
    
    if (homeTeam === awayTeam) { setError("Home and away teams must be different."); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await fetch(`${API_URL}/predict/match`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam }),
      });
      const data = await res.json();
      data.error ? setError(data.error) : setResult(data);
    } catch {
      setError("Request failed. Confirm the backend is running.");
    } finally { setLoading(false); }
  }

  // Figure out which outcome won
  const probs = result ? Object.entries(result.probabilities) : [];
  const maxProb = probs.length ? Math.max(...probs.map(([,v]) => v)) : 0;

  function outcomeColor(outcome: string) {
    const k = outcome.toLowerCase();
    if (k.includes("home")) return "var(--accent)";
    if (k.includes("draw")) return "#7aab8a";
    return "var(--loss)";
  }

  function winnerTeam(): string | null {
    if (!result) return null;
    const outcome = result.predicted_outcome.toLowerCase();
    if (outcome.includes("home")) return result.home_team;
    if (outcome.includes("away")) return result.away_team;
    return null;
  }

  const winner = winnerTeam();

  return (
    <main style={{ maxWidth: "900px", margin: "0 auto", padding: "32px 16px" }}>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: "10px",
        color: "var(--text-muted)", letterSpacing: "0.1em",
        textTransform: "uppercase", marginBottom: "32px",
      }}>
        Match prediction
      </div>

      {/* Team picker: VS layout */}
      <div className="predict-grid" style={{
        display: "grid",
        gridTemplateColumns: "1fr auto 1fr",
        gap: "0",
        alignItems: "center",
        marginBottom: "28px",
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "16px",
        padding: "24px 16px",
        width: "100%",
        boxSizing: "border-box",
      }}>
        <TeamPicker label="Home team" value={homeTeam} teams={teams} onChange={v => { setHomeTeam(v); setResult(null); }} />

        {/* VS center */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "8px", padding: "0 20px" }}>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: "22px", fontWeight: 500,
            color: "var(--text-faint)", letterSpacing: "0.08em",
          }}>VS</div>
          {result && (
            <div style={{
              fontFamily: "var(--font-mono)", fontSize: "9px",
              color: "var(--text-faint)", textAlign: "center", lineHeight: 1.6,
            }}>
              elo<br/>
              <span style={{ color: "var(--text-muted)" }}>{result.home_elo}</span>
              {" · "}
              <span style={{ color: "var(--text-muted)" }}>{result.away_elo}</span>
            </div>
          )}
        </div>

        <TeamPicker label="Away team" value={awayTeam} teams={teams} onChange={v => { setAwayTeam(v); setResult(null); }} />
      </div>

      {/* Predict button */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "32px" }}>
       <button
          onClick={handlePredict}
          disabled={loading || !homeTeam || !awayTeam}
          style={{
            background: loading ? "var(--accent-dim)" : "var(--accent)",
            color: "#041a0e", fontWeight: 600, fontSize: "13px",
            padding: "12px 32px", borderRadius: "40px", border: "none",
            cursor: loading ? "not-allowed" : "pointer",
            fontFamily: "var(--font-mono)", letterSpacing: "0.05em",
            textTransform: "uppercase", opacity: (!homeTeam || !awayTeam) ? 0.4 : 1,
            transition: "all 0.2s", width: "100%", maxWidth: "280px",
          }}
        >
          {loading ? "Predicting…" : "Run Prediction"}
        </button>
      </div>

      {error && (
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--loss)", textAlign: "center", marginBottom: "24px" }}>
          {error}
        </p>
      )}

      {/* Result */}
      {result && (
        <div style={{
          border: "1px solid var(--border)", borderRadius: "16px",
          overflow: "hidden", background: "var(--surface)",
        }}>
          {/* Winner banner */}
          {winner && (
            <div style={{
              background: "rgba(0,201,122,0.08)",
              borderBottom: "1px solid var(--border)",
              padding: "14px 24px",
              display: "flex", alignItems: "center", gap: "12px",
            }}>
              <Flag team={winner} size={28} />
              <div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "2px" }}>
                  Predicted winner
                </div>
                <div style={{ fontSize: "16px", fontWeight: 500, color: "var(--text)" }}>{winner}</div>
              </div>
              <div style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "22px", color: "var(--accent)", fontWeight: 500 }}>
                {maxProb}%
              </div>
            </div>
          )}

          {/* Draw banner */}
          {!winner && (
            <div style={{
              background: "rgba(122,171,138,0.08)", borderBottom: "1px solid var(--border)",
              padding: "14px 24px", display: "flex", alignItems: "center", gap: "12px",
            }}>
              <div style={{ width: 36, height: 27, background: "var(--border)", borderRadius: "4px" }} />
              <div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "#7aab8a", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "2px" }}>
                  Most likely outcome
                </div>
                <div style={{ fontSize: "16px", fontWeight: 500, color: "var(--text)" }}>Draw</div>
              </div>
              <div style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: "22px", color: "#7aab8a", fontWeight: 500 }}>
                {maxProb}%
              </div>
            </div>
          )}

          {/* Probability bars */}
          <div style={{ padding: "24px" }}>
            <div style={{ marginBottom: "20px" }}>
              {probs.map(([outcome, pct], i) => (
                <ProbBar
                  key={outcome}
                  label={outcome}
                  pct={pct}
                  color={outcomeColor(outcome)}
                  delay={i * 100}
                />
              ))}
            </div>

            {/* Head to head visual */}
            <div style={{
              display: "flex", alignItems: "center", gap: "12px",
              marginBottom: "20px", padding: "14px 16px",
              background: "rgba(0,0,0,0.2)", borderRadius: "10px",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
                <Flag team={result.home_team} size={22} />
                <span style={{ fontSize: "12px", color: "var(--text-dim)" }}>{result.home_team}</span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", marginBottom: "4px" }}>ELO</span>
                <span style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-muted)" }}>
                  {result.home_elo} · {result.away_elo}
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1, justifyContent: "flex-end" }}>
                <span style={{ fontSize: "12px", color: "var(--text-dim)" }}>{result.away_team}</span>
                <Flag team={result.away_team} size={22} />
              </div>
            </div>

            {/* Summary */}
            <p style={{
              fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.7,
              fontFamily: "var(--font-mono)", borderTop: "1px solid var(--border)",
              paddingTop: "16px", margin: 0,
            }}>
              {result.summary}
            </p>
          </div>
        </div>
      )}
    </main>
  );
}