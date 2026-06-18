// app/page.tsx
//
// Server component: fetches data on the server at request time, not in
// the browser. This means the API_URL here can be the plain (non-public)
// env var if we wanted, but we're using NEXT_PUBLIC_ consistently since
// later pages (the predict form) will need browser-side fetching too.

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface Result {
  date: string;
  group: string;
  home: string;
  away: string;
  home_score: number;
  away_score: number;
}

interface Fixture {
  date: string;
  group: string;
  home: string;
  away: string;
}

async function getResults(): Promise<Result[]> {
  const res = await fetch(`${API_URL}/fixtures/results`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch results: ${res.status}`);
  const data = await res.json();
  return data.results;
}

async function getRemaining(): Promise<Fixture[]> {
  const res = await fetch(`${API_URL}/fixtures/remaining`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch remaining fixtures: ${res.status}`);
  const data = await res.json();
  return data.fixtures;
}

export default async function Home() {
  const [results, remaining] = await Promise.all([getResults(), getRemaining()]);

  return (
    <main className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-6">WC2026 Predictor</h1>

      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">Results so far ({results.length})</h2>
        <div className="space-y-2">
          {results.map((r, i) => (
            <div key={i} className="flex justify-between border-b border-gray-700 py-1 text-sm">
              <span>{r.date} · Group {r.group}</span>
              <span>
                {r.home} {r.home_score} - {r.away_score} {r.away}
              </span>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4">Upcoming fixtures ({remaining.length})</h2>
        <div className="space-y-2">
          {remaining.slice(0, 10).map((f, i) => (
            <div key={i} className="flex justify-between border-b border-gray-700 py-1 text-sm">
              <span>{f.date} · Group {f.group}</span>
              <span>{f.home} vs {f.away}</span>
            </div>
          ))}
        </div>
        <p className="text-gray-500 text-sm mt-2">Showing first 10 of {remaining.length}</p>
      </section>
    </main>
  );
}