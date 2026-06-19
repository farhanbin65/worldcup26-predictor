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
          @media (max-width: 480px) {
            .wc-nav-link {
              font-size: 10px !important;
              padding: 5px 8px !important;
            }
          }
          .fixture-row {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            background: transparent;
            transition: background 0.12s;
            gap: 8px;
            flex-wrap: wrap;
          }
          .fixture-row:hover { background: var(--surface); }
          .fixture-row:last-child { border-bottom: none; }
          .fixture-meta {
            font-family: var(--font-mono);
            font-size: 10px;
            color: var(--text-faint);
            width: 120px;
            flex-shrink: 0;
          }
          .fixture-home, .fixture-away {
            flex: 1;
            display: flex;
            align-items: center;
            gap: 7px;
            min-width: 0;
          }
          .fixture-home { justify-content: flex-end; }
          .fixture-home span, .fixture-away span {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 13px;
            color: var(--text-dim);
          }
          @media (max-width: 600px) {
            .fixture-meta {
              width: 100%;
              order: -1;
              margin-bottom: 4px;
            }
            .fixture-row { padding: 10px 8px; }
            .fixture-home span, .fixture-away span { font-size: 12px; }
          }
          .champion-card {
            border: 1px solid var(--accent-dim);
            border-radius: 12px;
            background: rgba(0,201,122,0.04);
            padding: 20px 24px;
            margin-bottom: 40px;
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 16px;
            align-items: center;
            cursor: pointer;
            transition: border-color 0.2s, background 0.2s;
            text-decoration: none;
          }
          .champion-card:hover {
            border-color: var(--accent);
            background: rgba(0,201,122,0.09);
          }
          @media (max-width: 600px) {
            .champion-card {
              grid-template-columns: 1fr !important;
              padding: 16px !important;
            }
            .champion-card > div:last-child {
              border-left: none !important;
              padding-left: 0 !important;
              border-top: 1px solid var(--border);
              padding-top: 12px !important;
              margin-top: 4px;
            }
          }
          .footer-link {
            font-family: var(--font-mono), monospace;
            font-size: 11px;
            color: var(--text-muted);
            text-decoration: none;
            transition: color 0.15s;
          }
          .footer-link:hover { color: var(--accent); }
          .stat-grid {
            display: grid;
            gap: 10px;
          }
          @media (max-width: 600px) {
            .stat-grid {
              grid-template-columns: 1fr !important;
            }
          }
          @media (max-width: 600px) {
            .predict-grid {
              grid-template-columns: 1fr !important;
              gap: 20px !important;
            }
            .predict-grid > div:nth-child(2) {
              flex-direction: row !important;
              padding: 0 !important;
            }
          }
            .predict-grid {
            overflow: hidden;
          }

          @media (max-width: 560px) {
            .predict-grid {
              grid-template-columns: 1fr !important;
              gap: 24px !important;
              padding: 20px 12px !important;
            }
            .predict-grid > div:nth-child(2) {
              flex-direction: row !important;
              justify-content: center !important;
              padding: 4px 0 !important;
              gap: 16px !important;
            }
          }

          body { overflow-x: hidden; }
          main { overflow-x: hidden; max-width: 100vw; }
          .scroll-hint { display: none; }
          @media (max-width: 900px) {
            .scroll-hint { display: block !important; }
          }
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
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "8px",
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
            whiteSpace: "nowrap",
          }}>
            <span style={{
              width: "8px", height: "8px",
              borderRadius: "50%",
              background: "var(--accent)",
              display: "inline-block",
              flexShrink: 0,
            }} />
            WC2026 <span style={{ color: "var(--accent)" }}>/</span> PREDICTOR
          </Link>

          <nav style={{
            display: "flex",
            gap: "2px",
            flexWrap: "wrap",
            justifyContent: "flex-end",
            
          }}>
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