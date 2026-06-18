"use client";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface Contender {
  team: string;
  champion_pct: number;
  final_pct: number;
  semifinal_pct: number;
  quarterfinal_pct: number;
  round_of_32_pct: number;
}

interface ContendersResponse {
  n_simulations: number;
  generated_at: string;
  top_contenders: Contender[];
}

// ISO 3166-1 alpha-2 codes for flagicons.lipis.dev
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
  "New Zealand": "nz", "South Africa": "za", "Czechia": "cz", "Slovakia": "sk",
  "Romania": "ro", "Hungary": "hu", "Slovenia": "si", "Albania": "al",
  "Georgia": "ge", "Iceland": "is", "Finland": "fi", "Greece": "gr",
  "Israel": "il", "Bosnia and Herzegovina": "ba",
};

function FlagImg({ team, size = 20 }: { team: string; size?: number }) {
  const code = TEAM_CODE[team];
  if (!code) return <span style={{ width: size, height: size, display: "inline-block", background: "var(--border)", borderRadius: "2px" }} />;
  return (
    <img
      src={`https://flagicons.lipis.dev/flags/4x3/${code}.svg`}
      alt={team}
      width={size}
      height={Math.round(size * 0.75)}
      style={{ borderRadius: "2px", objectFit: "cover", flexShrink: 0 }}
    />
  );
}

function TeamRow({
  team, pct, align = "left", isWinner = false, isTBD = false,
}: {
  team: string; pct?: number; align?: "left" | "right"; isWinner?: boolean; isTBD?: boolean;
}) {
  const tbd = isTBD || team.startsWith("W(") || team.startsWith("TBD") || team === "TBD";
  return (
    <div style={{
      display: "flex",
      flexDirection: align === "right" ? "row-reverse" : "row",
      alignItems: "center",
      gap: "7px",
      padding: "6px 10px",
      background: isWinner ? "rgba(0,201,122,0.08)" : "transparent",
      borderBottom: "1px solid var(--border)",
      transition: "background 0.12s",
    }}>
      {!tbd && <FlagImg team={team} size={18} />}
      {tbd && <span style={{ width: 18, height: 14, background: "var(--border)", borderRadius: "2px", opacity: 0.4, flexShrink: 0 }} />}
      <span style={{
        flex: 1,
        fontSize: "11px",
        fontStyle: tbd ? "italic" : "normal",
        color: tbd ? "var(--text-faint)" : isWinner ? "var(--text)" : "var(--text-dim)",
        textAlign: align === "right" ? "right" : "left",
        overflow: "hidden",
        textOverflow: "ellipsis",
        whiteSpace: "nowrap",
      }}>
        {tbd ? "TBD" : team}
      </span>
      {pct !== undefined && !tbd && (
        <span style={{
          fontFamily: "var(--font-mono)",
          fontSize: "9px",
          color: isWinner ? "var(--accent)" : "var(--text-faint)",
          flexShrink: 0,
        }}>{pct}%</span>
      )}
    </div>
  );
}

function MatchBox({
  home, away, date, homePct, awayPct, isFinal = false, align = "left",
}: {
  home: string; away: string; date: string;
  homePct?: number; awayPct?: number;
  isFinal?: boolean; align?: "left" | "right";
}) {
  const homeWins = homePct !== undefined && awayPct !== undefined && homePct > awayPct;
  const awayWins = homePct !== undefined && awayPct !== undefined && awayPct > homePct;
  return (
    <div style={{
      border: `1px solid ${isFinal ? "var(--accent-dim)" : "var(--border)"}`,
      borderRadius: "8px",
      background: isFinal ? "rgba(0,201,122,0.05)" : "var(--surface)",
      overflow: "hidden",
      width: "160px",
      flexShrink: 0,
    }}>
      <div style={{
        fontFamily: "var(--font-mono)", fontSize: "9px",
        color: "var(--text-faint)", padding: "3px 8px",
        background: "rgba(0,0,0,0.2)", borderBottom: "1px solid var(--border)",
      }}>{date}</div>
      <TeamRow team={home} pct={homePct} align={align} isWinner={homeWins} />
      <TeamRow team={away} pct={awayPct} align={align} isWinner={awayWins} />
    </div>
  );
}

// Vertical connector between pairs of matches
function VConnector({ count }: { count: number }) {
  return (
    <div style={{ width: "24px", display: "flex", flexDirection: "column", alignSelf: "stretch" }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{
          flex: 1,
          borderTop: i % 2 !== 0 ? "1px solid var(--border)" : "none",
          borderRight: "1px solid var(--border)",
          borderBottom: i % 2 === 0 ? "1px solid var(--border)" : "none",
        }} />
      ))}
    </div>
  );
}

function LeftConnector({ pairs }: { pairs: number }) {
  return (
    <div style={{ width: "24px", display: "flex", flexDirection: "column", alignSelf: "stretch" }}>
      {Array.from({ length: pairs }).map((_, pi) => (
        <div key={pi} style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <div style={{ flex: 1, borderRight: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }} />
          <div style={{ flex: 1, borderRight: "1px solid var(--border)", borderTop: "1px solid var(--border)" }} />
        </div>
      ))}
    </div>
  );
}

function RightConnector({ pairs }: { pairs: number }) {
  return (
    <div style={{ width: "24px", display: "flex", flexDirection: "column", alignSelf: "stretch" }}>
      {Array.from({ length: pairs }).map((_, pi) => (
        <div key={pi} style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <div style={{ flex: 1, borderLeft: "1px solid var(--border)", borderBottom: "1px solid var(--border)" }} />
          <div style={{ flex: 1, borderLeft: "1px solid var(--border)", borderTop: "1px solid var(--border)" }} />
        </div>
      ))}
    </div>
  );
}

function HBar() {
  return <div style={{ width: "24px", height: "1px", background: "var(--border)", alignSelf: "center", flexShrink: 0 }} />;
}

export default function TournamentPage() {
  const [data, setData] = useState<ContendersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"bracket" | "odds">("bracket");

  useEffect(() => {
    fetch(`${API_URL}/tournament/contenders?limit=20`)
      .then(r => r.json()).then(setData).catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const top = data?.top_contenders ?? [];
  const maxPct = top[0]?.champion_pct ?? 1;

  function t(i: number) { return top[i]?.team ?? "TBD"; }
  function pct(i: number, field: keyof Contender): number | undefined {
    const v = top[i]?.[field];
    return typeof v === "number" ? v : undefined;
  }

  // Left half: teams 0-7 (top bracket)
  // Right half: teams 8-15 (bottom bracket)
  const leftR32 = [
    { home: t(0), away: t(1), date: "9 Jul",  hp: pct(0,"round_of_32_pct"), ap: pct(1,"round_of_32_pct") },
    { home: t(2), away: t(3), date: "9 Jul",  hp: pct(2,"round_of_32_pct"), ap: pct(3,"round_of_32_pct") },
    { home: t(4), away: t(5), date: "10 Jul", hp: pct(4,"round_of_32_pct"), ap: pct(5,"round_of_32_pct") },
    { home: t(6), away: t(7), date: "10 Jul", hp: pct(6,"round_of_32_pct"), ap: pct(7,"round_of_32_pct") },
  ];
  const rightR32 = [
    { home: t(8),  away: t(9),  date: "11 Jul", hp: pct(8,"round_of_32_pct"),  ap: pct(9,"round_of_32_pct") },
    { home: t(10), away: t(11), date: "11 Jul", hp: pct(10,"round_of_32_pct"), ap: pct(11,"round_of_32_pct") },
    { home: t(12), away: t(13), date: "12 Jul", hp: pct(12,"round_of_32_pct"), ap: pct(13,"round_of_32_pct") },
    { home: t(14), away: t(15), date: "12 Jul", hp: pct(14,"round_of_32_pct"), ap: pct(15,"round_of_32_pct") },
  ];
  const leftQF = [
    { home: t(0), away: t(2), date: "14 Jul", hp: pct(0,"quarterfinal_pct"), ap: pct(2,"quarterfinal_pct") },
    { home: t(4), away: t(6), date: "14 Jul", hp: pct(4,"quarterfinal_pct"), ap: pct(6,"quarterfinal_pct") },
  ];
  const rightQF = [
    { home: t(8),  away: t(10), date: "15 Jul", hp: pct(8,"quarterfinal_pct"),  ap: pct(10,"quarterfinal_pct") },
    { home: t(12), away: t(14), date: "15 Jul", hp: pct(12,"quarterfinal_pct"), ap: pct(14,"quarterfinal_pct") },
  ];
  const leftSF  = { home: t(0), away: t(4), date: "18 Jul", hp: pct(0,"semifinal_pct"), ap: pct(4,"semifinal_pct") };
  const rightSF = { home: t(8), away: t(12), date: "18 Jul", hp: pct(8,"semifinal_pct"), ap: pct(12,"semifinal_pct") };
  const final   = { home: t(0), away: t(8), date: "19 Jul", hp: pct(0,"final_pct"), ap: pct(8,"final_pct") };

  return (
    <main style={{ maxWidth: "1300px", margin: "0 auto", padding: "40px 24px" }}>

      {/* Header */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "4px" }}>
          Tournament
        </div>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-faint)" }}>
          {data ? `${data.n_simulations.toLocaleString()} monte carlo simulations · ${data.generated_at}` : "Loading simulation data…"}
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "10px", marginBottom: "24px" }}>
        {[
          { label: "Simulations", value: "10K", sub: "monte carlo runs" },
          { label: "Log loss", value: "0.8622", sub: "vs 1.0986 random" },
          { label: "Teams", value: "48", sub: "104 matches total" },
        ].map(c => (
          <div key={c.label} style={{ border: "1px solid var(--border)", background: "var(--surface)", borderRadius: "10px", padding: "14px 16px" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--text-faint)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "6px" }}>{c.label}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "22px", color: "var(--accent)", fontWeight: 500, lineHeight: 1, marginBottom: "4px" }}>{c.value}</div>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)" }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "4px", marginBottom: "28px" }}>
        {(["bracket","odds"] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            fontFamily: "var(--font-mono)", fontSize: "11px", letterSpacing: "0.06em",
            textTransform: "uppercase", padding: "6px 14px", borderRadius: "20px",
            border: "1px solid", cursor: "pointer", transition: "all 0.15s",
            borderColor: activeTab === tab ? "var(--accent)" : "var(--border)",
            background: activeTab === tab ? "rgba(0,201,122,0.1)" : "transparent",
            color: activeTab === tab ? "var(--accent)" : "var(--text-muted)",
          }}>
            {tab === "bracket" ? "Bracket" : "Odds"}
          </button>
        ))}
      </div>

      {/* BRACKET */}
      {activeTab === "bracket" && (
        <>
          {loading ? (
            <p style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-faint)" }}>Loading predictions…</p>
          ) : (
            <div style={{ overflowX: "auto", paddingBottom: "16px" }}>

              {/* Round labels */}
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px", minWidth: "900px" }}>
                {["R32","QF","SF","","SF","QF","R32"].map((lbl, i) => (
                  <span key={i} style={{
                    fontFamily: "var(--font-mono)", fontSize: "9px",
                    color: lbl ? "var(--text-muted)" : "transparent",
                    textTransform: "uppercase", letterSpacing: "0.08em",
                    flex: 1, textAlign: "center",
                  }}>{lbl || "FINAL"}</span>
                ))}
              </div>

              {/* Main bracket: left half | trophy center | right half */}
              <div style={{ display: "flex", alignItems: "center", gap: "0", minWidth: "900px" }}>

                {/* ── LEFT HALF (reads left → right toward center) ── */}
                {/* R32 left */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {leftR32.map((m, i) => (
                    <MatchBox key={i} home={m.home} away={m.away} date={m.date} homePct={m.hp} awayPct={m.ap} />
                  ))}
                </div>

                <LeftConnector pairs={2} />

                {/* QF left */}
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-around", gap: "0", alignSelf: "stretch" }}>
                  <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
                    <MatchBox home={leftQF[0].home} away={leftQF[0].away} date={leftQF[0].date} homePct={leftQF[0].hp} awayPct={leftQF[0].ap} />
                  </div>
                  <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
                    <MatchBox home={leftQF[1].home} away={leftQF[1].away} date={leftQF[1].date} homePct={leftQF[1].hp} awayPct={leftQF[1].ap} />
                  </div>
                </div>

                <LeftConnector pairs={1} />

                {/* SF left */}
                <div style={{ display: "flex", alignItems: "center", alignSelf: "stretch" }}>
                  <MatchBox home={leftSF.home} away={leftSF.away} date={leftSF.date} homePct={leftSF.hp} awayPct={leftSF.ap} />
                </div>

                <HBar />

                {/* ── CENTER: FINAL + trophy ── */}
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px", flexShrink: 0 }}>
                  {/* Trophy SVG */}
                  <div style={{ fontSize: "36px", lineHeight: 1, filter: "drop-shadow(0 0 8px rgba(0,201,122,0.3))" }}>🏆</div>
                  <div style={{
                    fontFamily: "var(--font-mono)", fontSize: "9px",
                    color: "var(--accent)", letterSpacing: "0.12em",
                    textTransform: "uppercase", marginBottom: "4px",
                  }}>Final · 19 Jul</div>
                  <MatchBox home={final.home} away={final.away} date="19 Jul" homePct={final.hp} awayPct={final.ap} isFinal />
                </div>

                <HBar />

                {/* ── RIGHT HALF (reads right → left toward center) ── */}
                {/* SF right */}
                <div style={{ display: "flex", alignItems: "center", alignSelf: "stretch" }}>
                  <MatchBox home={rightSF.home} away={rightSF.away} date={rightSF.date} homePct={rightSF.hp} awayPct={rightSF.ap} align="right" />
                </div>

                <RightConnector pairs={1} />

                {/* QF right */}
                <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-around", alignSelf: "stretch" }}>
                  <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
                    <MatchBox home={rightQF[0].home} away={rightQF[0].away} date={rightQF[0].date} homePct={rightQF[0].hp} awayPct={rightQF[0].ap} align="right" />
                  </div>
                  <div style={{ flex: 1, display: "flex", alignItems: "center" }}>
                    <MatchBox home={rightQF[1].home} away={rightQF[1].away} date={rightQF[1].date} homePct={rightQF[1].hp} awayPct={rightQF[1].ap} align="right" />
                  </div>
                </div>

                <RightConnector pairs={2} />

                {/* R32 right */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {rightR32.map((m, i) => (
                    <MatchBox key={i} home={m.home} away={m.away} date={m.date} homePct={m.hp} awayPct={m.ap} align="right" />
                  ))}
                </div>
              </div>

              <p style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", marginTop: "16px" }}>
                Teams ranked by Monte Carlo championship probability · % shows round-reach likelihood from 10,000 simulations
              </p>
            </div>
          )}
        </>
      )}

      {/* ODDS leaderboard */}
      {activeTab === "odds" && (
        <div style={{ maxWidth: "680px" }}>
          {loading && <p style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-faint)" }}>Loading…</p>}
          {!loading && top.length === 0 && (
            <div style={{ border: "1px solid var(--border)", borderRadius: "10px", padding: "16px 20px", fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-muted)" }}>
              Backend warming up.{" "}
              <a href="https://worldcup26-predictor.onrender.com/docs" target="_blank" rel="noopener noreferrer"
                style={{ color: "var(--accent)", textDecoration: "underline", textUnderlineOffset: "3px" }}>
                Wake it here
              </a>, then refresh.
            </div>
          )}
          {top.map((c, i) => {
            const barW = (c.champion_pct / maxPct) * 100;
            const isTop = i === 0;
            return (
              <div key={c.team} style={{
                padding: "10px 12px", borderRadius: "8px", marginBottom: "2px",
                border: isTop ? "1px solid var(--border)" : "1px solid transparent",
                background: isTop ? "var(--surface)" : "transparent",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)", width: "20px", textAlign: "right" }}>{i + 1}</span>
                  <FlagImg team={c.team} size={20} />
                  <span style={{ flex: 1, fontSize: "13px", color: isTop ? "var(--text)" : "var(--text-dim)" }}>{c.team}</span>
                  {isTop && (
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "9px", color: "var(--accent)", border: "1px solid var(--border)", borderRadius: "4px", padding: "1px 6px" }}>most likely</span>
                  )}
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", fontWeight: 500, color: isTop ? "var(--accent)" : "var(--text-muted)", minWidth: "50px", textAlign: "right" }}>{c.champion_pct}%</span>
                </div>
                <div style={{ marginLeft: "62px", height: "3px", background: "var(--border)", borderRadius: "2px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${barW}%`, background: isTop ? "var(--accent)" : "var(--accent-dim)", borderRadius: "2px", transition: "width 0.6s ease" }} />
                </div>
                <div style={{ marginLeft: "62px", marginTop: "5px", display: "flex", gap: "14px", fontFamily: "var(--font-mono)", fontSize: "10px", color: "var(--text-faint)" }}>
                  <span>Final <span style={{ color: "var(--text-muted)" }}>{c.final_pct}%</span></span>
                  <span>SF <span style={{ color: "var(--text-muted)" }}>{c.semifinal_pct}%</span></span>
                  <span>QF <span style={{ color: "var(--text-muted)" }}>{c.quarterfinal_pct}%</span></span>
                  <span>R32 <span style={{ color: "var(--text-muted)" }}>{c.round_of_32_pct}%</span></span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}
