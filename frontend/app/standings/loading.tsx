export default function Loading() {
  return (
    <main style={{ maxWidth: "900px", margin: "0 auto", padding: "40px 24px" }}>
      <style>{`
        @keyframes pulse { 0%,100% { opacity:0.4; } 50% { opacity:0.8; } }
        .skeleton { background: var(--surface); border-radius: 6px; animation: pulse 1.5s ease-in-out infinite; }
      `}</style>

      <div className="skeleton" style={{ width: "150px", height: "10px", marginBottom: "24px" }} />

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: "12px",
      }}>
        {Array.from({ length: 6 }).map((_, g) => (
          <div key={g} style={{ border: "1px solid var(--border)", borderRadius: "10px", padding: "16px" }}>
            <div className="skeleton" style={{ width: "80px", height: "14px", marginBottom: "16px" }} />
            {Array.from({ length: 4 }).map((_, r) => (
              <div key={r} style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
                <div className="skeleton" style={{ flex: 1, height: "12px" }} />
                <div className="skeleton" style={{ width: "20px", height: "12px" }} />
                <div className="skeleton" style={{ width: "20px", height: "12px" }} />
              </div>
            ))}
          </div>
        ))}
      </div>
    </main>
  );
}