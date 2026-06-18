// app/tournament/page.tsx
//
// Server component displaying the precomputed Monte Carlo tournament
// probabilities (10,000 simulations) as a ranked leaderboard.

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface TeamStats {
  champion_pct: number;
  final_pct: number;
  semifinal_pct: number;
  quarterfinal_pct: number;
  round_of_32_pct: number;
}

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

async function getContenders(): Promise<ContendersResponse> {
  const res = await fetch(`${API_URL}/tournament/contenders?limit=20`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch tournament probabilities: ${res.status}`);
  return res.json();
}

export default async function TournamentPage() {
  const { n_simulations, generated_at, top_contenders } = await getContenders();

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-2">Tournament Winner Odds</h1>
      <p className="text-sm text-gray-500 mb-6">
        Based on {n_simulations.toLocaleString()} Monte Carlo simulations · generated {generated_at}
      </p>

      <table className="w-full text-sm max-w-3xl">
        <thead>
          <tr className="text-gray-400 text-left border-b border-gray-700">
            <th className="py-2">#</th>
            <th className="py-2">Team</th>
            <th className="py-2 text-right">Champion</th>
            <th className="py-2 text-right">Final</th>
            <th className="py-2 text-right">SF</th>
            <th className="py-2 text-right">QF</th>
            <th className="py-2 text-right">R32</th>
          </tr>
        </thead>
        <tbody>
          {top_contenders.map((c, i) => (
            <tr key={c.team} className="border-b border-gray-800">
              <td className="py-2 text-gray-500">{i + 1}</td>
              <td className="py-2 font-medium">{c.team}</td>
              <td className="py-2 text-right font-mono">{c.champion_pct}%</td>
              <td className="py-2 text-right font-mono text-gray-400">{c.final_pct}%</td>
              <td className="py-2 text-right font-mono text-gray-400">{c.semifinal_pct}%</td>
              <td className="py-2 text-right font-mono text-gray-400">{c.quarterfinal_pct}%</td>
              <td className="py-2 text-right font-mono text-gray-400">{c.round_of_32_pct}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}