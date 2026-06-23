"use client";
import { useState, useEffect } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface Result { date: string; group: string; home: string; away: string; home_score: number; away_score: number; }
interface Fixture { date: string; group: string; home: string; away: string; }
interface Contender { team: string; champion_pct: number; final_pct: number; semifinal_pct: number; }

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
  "Cape Verde": "cv",
};

function Flag({ team, size = 18 }: { team: string; size?: number }) {
  const code = TEAM_CODE[team];
  if (!code) return <span style={{ display: "inline-block", width: size, height: Math.round(size * 0.75), background: "var(--border)", borderRadius: "2px", flexShrink: 0 }} />;
  return <img src={`https://flagicons.lipis.dev/flags/4x3/${code}.svg`} alt={team} width={Math.round(size * 1.33)} height={size} style={{ borderRadius: "2px", objectFit: "cover", flexShrink: 0, display: "block" }} />;
}

export default function Home() {
  const [results, setResults] = useState<Result[]>([]);
  const [remaining, setRemaining] = useState<Fixture[]>([]);
  const [contenders, setContenders] = useState<Contender[]>([]);
  const [showAllResults, setShowAllResults] = useState(false);
  const [loading, setLoading] = useState(true);
  const [backendDown, setBackendDown] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch(`${API_URL}/fixtures/results`).then(r => r.json()).catch(() => null),
      fetch(`${API_URL}/fixtures/remaining`).then(r => r.json()).catch(() => null),
      fetch(`${API_URL}/tournament/contenders?limit=3`).then(r => r.json()).catch(() => null),
    ]).then(([r, f, c]) => {
      const res = r?.results ?? [];
      const fix = f?.fixtures ?? [];
      const con = c?.top_contenders ?? [];
      setResults(res);
      setRemaining(fix);
      setContenders(con);
      if (res.length === 0 && fix.length === 0) setBackendDown(true);
    }).finally(() => setLoading(false));
  }, []);

  const winner = contenders[0];
  const runner = contenders[1];
  const third  = contenders[2];

  // Sort results newest first, show last 10 unless expanded
  const sortedResults = [...results].sort((a, b) => b.date.localeCompare(a.date));
  const visibleResults = showAllResults ? sortedResults : sortedResults.slice(0, 10);

  if (loading) return (
    <main style={{ maxWidth: "900px", margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)", padding: "12px 0", marginBottom: "32px" }}>
        Loading…
      </div>
    </main>
  );

  return (
    <main style={{ maxWidth: "900px", margin: "0 auto", padding: "40px 24px" }}>

      {/* Model strip */}
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)",
        borderTop: "1px solid var(--border)", borderBottom: "1px solid var(--border)",
        padding: "12px 0", marginBottom: "32px",
        display: "flex", flexWrap: "wrap", gap: "0 20px",
      }}>
        <span style={{ color: "var(--text-dim)" }}>{results.length} results logged</span>
        <span style={{ color: "var(--border)" }}>·</span>
        <span style={{ color: "var(--text-dim)" }}>{remaining.length} fixtures remaining</span>
        <span style={{ color: "var(--border)" }}>·</span>
        <span>model: logistic regression</span>
        <span style={{ color: "var(--border)" }}>·</span>
        <span>log loss <span style={{ color: "var(--accent)" }}>0.8622</span></span>
      </div>

      {/* Predicted winner card */}
      {winner && (
        <Link href="/tournament" className="champion-card">
          <div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "10px", display: "flex", alignItems: "center", gap: "8px" }}>
              Predicted champion · 10,000 simulations
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-faint)", marginLeft: "auto" }}>View bracket →</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "14px", marginBottom: "12px" }}>
              <Flag team={winner.team} size={52} />
              <div>
                <div style={{ fontSize: "24px", fontWeight: 500, color: "var(--text)", lineHeight: 1.1 }}>{winner.team}</div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "20px", color: "var(--accent)", marginTop: "2px" }}>{winner.champion_pct}%</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: "20px", fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-faint)" }}>
              <span>Final <span style={{ color: "var(--text-muted)" }}>{winner.final_pct}%</span></span>
              <span>Semi-final <span style={{ color: "var(--text-muted)" }}>{winner.semifinal_pct}%</span></span>
            </div>
          </div>
          {runner && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", borderLeft: "1px solid var(--border)", paddingLeft: "20px" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-faint)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "4px" }}>Also likely</div>
              {[runner, third].filter(Boolean).map((c) => (
                <div key={c.team} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Flag team={c.team} size={22} />
                  <span style={{ fontSize: "12px", color: "var(--text-dim)", flex: 1 }}>{c.team}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>{c.champion_pct}%</span>
                </div>
              ))}
            </div>
          )}
        </Link>
      )}

      {backendDown && (
        <div style={{ border: "1px solid var(--border)", borderRadius: "10px", padding: "16px 20px", marginBottom: "32px", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-muted)" }}>
          Backend warming up.{" "}
          <a href="https://worldcup26-predictor.onrender.com/docs" target="_blank" rel="noopener noreferrer" style={{ color: "var(--accent)", textDecoration: "underline", textUnderlineOffset: "3px" }}>Wake it here</a>, then refresh.
        </div>
      )}

      {!backendDown && (
        <>
          {/* Results */}
          <section style={{ marginBottom: "48px" }}>
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: "12px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                Results so far
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>{results.length}</span>
            </div>

            <div style={{ border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
              {visibleResults.map((r, i) => (
                <div key={i} className="fixture-row">
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", width: "120px", flexShrink: 0 }}>
                    {r.date} · GRP {r.group}
                  </span>
                  <div className="fixture-home">
                    <span>{r.home}</span>
                    <Flag team={r.home} size={18} />
                  </div>
                  <span style={{
                    fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 500,
                    color: "var(--text)", background: "var(--surface)",
                    border: "1px solid var(--border)", borderRadius: "8px",
                    padding: "3px 12px", minWidth: "64px", textAlign: "center", flexShrink: 0,
                  }}>
                    {r.home_score} – {r.away_score}
                  </span>
                  <div className="fixture-away">
                    <Flag team={r.away} size={18} />
                    <span>{r.away}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Toggle */}
            {results.length > 10 && (
              <button
                onClick={() => setShowAllResults(v => !v)}
                style={{
                  marginTop: "10px",
                  background: "none",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-muted)",
                  fontFamily: "var(--font-mono)",
                  fontSize: "11px",
                  padding: "6px 14px",
                  cursor: "pointer",
                  transition: "all 0.15s",
                  width: "100%",
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--accent)";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--accent)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "var(--border)";
                  (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted)";
                }}
              >
                {showAllResults ? `Show less` : `Show all ${results.length} results`}
              </button>
            )}
          </section>

          {/* Upcoming */}
          <section>
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: "12px" }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
                Upcoming fixtures
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-muted)" }}>{remaining.length} total</span>
            </div>

            <div style={{ border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
              {remaining.slice(0, 10).map((f, i) => (
                <div key={i} className="fixture-row">
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", width: "120px", flexShrink: 0 }}>
                    {f.date} · GRP {f.group}
                  </span>
                  <div className="fixture-home">
                    <span>{f.home}</span>
                    <Flag team={f.home} size={18} />
                  </div>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", width: "28px", textAlign: "center", flexShrink: 0 }}>vs</span>
                  <div className="fixture-away">
                    <Flag team={f.away} size={18} />
                    <span>{f.away}</span>
                  </div>
                </div>
              ))}
            </div>
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", marginTop: "12px", paddingLeft: "12px" }}>
              showing first 10 of {remaining.length}
            </p>
          </section>

          {/* Footer */}
          <footer style={{ marginTop: "80px", paddingTop: "24px", borderTop: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-faint)" }}>
              WC2026 Predictor · 10,000 Monte Carlo simulations · Logistic regression model
            </span>
            <a href="https://farhanbin.dev" target="_blank" rel="noopener noreferrer" className="footer-link">
              Built by Farhan · farhanbin.dev
            </a>
          </footer>
        </>
      )}
    </main>
  );
}