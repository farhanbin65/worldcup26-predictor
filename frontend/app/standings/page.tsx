// app/standings/page.tsx
//
// Server component fetching live group tables from the backend.

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
  const res = await fetch(`${API_URL}/standings/`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch standings: ${res.status}`);
  return res.json();
}

export default async function StandingsPage() {
  const { groups } = await getStandings();

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Group Standings</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(groups).map(([letter, table]) => (
          <div key={letter} className="border border-gray-700 rounded p-4">
            <h2 className="text-lg font-semibold mb-3">Group {letter}</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left">
                  <th className="pb-1">Team</th>
                  <th className="pb-1 text-center">P</th>
                  <th className="pb-1 text-center">GD</th>
                  <th className="pb-1 text-center">Pts</th>
                </tr>
              </thead>
              <tbody>
                {table.map((t, i) => (
                  <tr key={t.team} className={i < 2 ? "text-white" : "text-gray-500"}>
                    <td className="py-0.5">{t.team}</td>
                    <td className="py-0.5 text-center">{t.played}</td>
                    <td className="py-0.5 text-center">
                      {t.goal_diff > 0 ? `+${t.goal_diff}` : t.goal_diff}
                    </td>
                    <td className="py-0.5 text-center">{t.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </main>
  );
}