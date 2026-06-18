// app/components/Nav.tsx
import Link from "next/link";

export default function Nav() {
  return (
    <nav className="border-b border-gray-800 px-8 py-4 flex gap-6 text-sm">
      <Link href="/" className="text-white hover:text-gray-300 font-medium">
        WC2026 Predictor
      </Link>
      <Link href="/standings" className="text-gray-400 hover:text-white">
        Standings
      </Link>
      <Link href="/predict" className="text-gray-400 hover:text-white">
        Predict
      </Link>
      <Link href="/tournament" className="text-gray-400 hover:text-white">
        Tournament Odds
      </Link>
    </nav>
  );
}