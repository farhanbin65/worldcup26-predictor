// app/standings/page.tsx

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface TeamStanding {
  team: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
}

interface GroupsResponse {
  groups: Record<string, TeamStanding[]>;
}

async function getStandings(): Promise<GroupsResponse> {
  try {
    const res = await fetch(`${API_URL}/standings/`, { cache: "no-store" });
    if (!res.ok) return { groups: {} };
    return res.json();
  } catch {
    return { groups: {} };
  }
}

export default async function StandingsPage() {
  const { groups } = await getStandings();
  const groupEntries = Object.entries(groups);

  return (
    <main className="max-w-4xl mx-auto px-6 py-10">
      <div className="font-mono text-[10px] text-[#4d7a5c] uppercase tracking-widest mb-8">
        Group standings
      </div>

      {groupEntries.length === 0 && (
        <div className="border border-[#1a3025] rounded-lg px-5 py-4 text-sm text-[#4d7a5c] font-mono">
          Backend warming up.{" "}
          <a
            href="https://worldcup26-predictor.onrender.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[#00c97a] underline underline-offset-2"
          >
            Wake it here
          </a>
          , then refresh.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {groupEntries.map(([letter, table]) => (
          <div
            key={letter}
            className="border border-[#1a3025] bg-[#0a1510] rounded-xl overflow-hidden"
          >
            {/* Group header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[#1a3025]">
              <span className="font-mono text-xs text-[#7aab8a] uppercase tracking-widest">
                Group {letter}
              </span>
              <span className="font-mono text-[10px] text-[#3d5e49]">
                {table.filter(t => t.played > 0).length}/{table.length} played
              </span>
            </div>

            {/* Column headers */}
            <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-0 px-4 pt-2.5 pb-1">
              <span className="font-mono text-[9px] text-[#3d5e49] uppercase tracking-widest">Team</span>
              <span className="font-mono text-[9px] text-[#3d5e49] uppercase tracking-widest w-6 text-center">P</span>
              <span className="font-mono text-[9px] text-[#3d5e49] uppercase tracking-widest w-6 text-center">W</span>
              <span className="font-mono text-[9px] text-[#3d5e49] uppercase tracking-widest w-8 text-center">GD</span>
              <span className="font-mono text-[9px] text-[#3d5e49] uppercase tracking-widest w-8 text-center">Pts</span>
            </div>

            {/* Rows */}
            <div className="px-2 pb-2">
              {table.map((t, i) => {
                const isQualifying = i < 2;
                const isThird = i === 2;
                return (
                  <div
                    key={t.team}
                    className="grid grid-cols-[1fr_auto_auto_auto_auto] items-center gap-0 px-2 py-1.5 rounded-md"
                  >
                    {/* Qualification indicator + name */}
                    <div className="flex items-center gap-2 min-w-0">
                      <div
                        className={`w-1 h-4 rounded-full flex-shrink-0 ${
                          isQualifying
                            ? "bg-[#00c97a]"
                            : isThird
                            ? "bg-[#4d7a5c]"
                            : "bg-transparent"
                        }`}
                      />
                      <span
                        className={`text-xs truncate ${
                          isQualifying
                            ? "text-[#c8d8cc]"
                            : isThird
                            ? "text-[#7aab8a]"
                            : "text-[#3d5e49]"
                        }`}
                      >
                        {t.team}
                      </span>
                    </div>

                    <span className="font-mono text-xs text-[#4d7a5c] w-6 text-center">{t.played}</span>
                    <span className="font-mono text-xs text-[#4d7a5c] w-6 text-center">{t.won}</span>
                    <span
                      className={`font-mono text-xs w-8 text-center ${
                        t.goal_diff > 0
                          ? "text-[#00c97a]"
                          : t.goal_diff < 0
                          ? "text-[#c0634a]"
                          : "text-[#4d7a5c]"
                      }`}
                    >
                      {t.goal_diff > 0 ? `+${t.goal_diff}` : t.goal_diff}
                    </span>
                    <span
                      className={`font-mono text-xs w-8 text-center font-medium ${
                        isQualifying ? "text-[#e8ede9]" : "text-[#4d7a5c]"
                      }`}
                    >
                      {t.points}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 px-4 py-2 border-t border-[#0f1f15]">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-[#00c97a]" />
                <span className="font-mono text-[9px] text-[#3d5e49]">Qualifies</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-[#4d7a5c]" />
                <span className="font-mono text-[9px] text-[#3d5e49]">3rd place (best)</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}