import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
});

export const metadata: Metadata = {
  title: "WC2026 Predictor",
  description: "Calibrated match predictions and Monte Carlo tournament simulation for FIFA World Cup 2026.",
};

const nav = [
  { href: "/", label: "Results" },
  { href: "/standings", label: "Standings" },
  { href: "/predict", label: "Predict" },
  { href: "/tournament", label: "Tournament" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${plexMono.variable}`}>
        <style>{`
          .wc-nav-link {
            font-family: var(--font-mono), monospace;
            font-size: 12px;
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            transition: color 0.15s, background 0.15s;
          }
          .wc-nav-link:hover {
            color: var(--text);
            background: var(--surface-hover);
          }
          .fixture-row {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            background: transparent;
            transition: background 0.12s;
            gap: 12px;
          }
          .fixture-row:hover { background: var(--surface); }
          .fixture-row:last-child { border-bottom: none; }
        `}</style>

        <header style={{
          borderBottom: "1px solid var(--border)",
          position: "sticky",
          top: 0,
          background: "rgba(13,26,20,0.96)",
          backdropFilter: "blur(8px)",
          zIndex: 10,
        }}>
          <div style={{
            maxWidth: "900px",
            margin: "0 auto",
            padding: "14px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}>
            <Link href="/" style={{
              fontFamily: "var(--font-mono), monospace",
              fontSize: "13px",
              color: "var(--text)",
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              letterSpacing: "0.04em",
            }}>
              <span style={{
                width: "8px", height: "8px",
                borderRadius: "50%",
                background: "var(--accent)",
                display: "inline-block",
                flexShrink: 0,
              }} />
              WC2026{" "}
              <span style={{ color: "var(--accent)" }}>/</span>
              {" "}PREDICTOR
            </Link>

            <nav style={{ display: "flex", gap: "4px" }}>
              {nav.map((link) => (
                <Link key={link.href} href={link.href} className="wc-nav-link">
                  {link.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>

        {children}
      </body>
    </html>
  );
}