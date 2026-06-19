export default function Loading() {
  return (
    <main style={{ maxWidth: "900px", margin: "0 auto", padding: "40px 24px" }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
        .skeleton {
          background: var(--surface);
          border-radius: 6px;
          animation: pulse 1.5s ease-in-out infinite;
        }
      `}</style>

      {/* Model strip skeleton */}
      <div style={{
        borderTop: "1px solid var(--border)",
        borderBottom: "1px solid var(--border)",
        padding: "12px 0",
        marginBottom: "32px",
      }}>
        <div className="skeleton" style={{ width: "60%", height: "14px" }} />
      </div>

      {/* Champion card skeleton */}
      <div style={{
        border: "1px solid var(--border)",
        borderRadius: "12px",
        padding: "20px 24px",
        marginBottom: "40px",
      }}>
        <div className="skeleton" style={{ width: "180px", height: "10px", marginBottom: "14px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div className="skeleton" style={{ width: "52px", height: "39px", borderRadius: "4px" }} />
          <div>
            <div className="skeleton" style={{ width: "140px", height: "22px", marginBottom: "8px" }} />
            <div className="skeleton" style={{ width: "60px", height: "18px" }} />
          </div>
        </div>
      </div>

      {/* Results list skeleton */}
      <div style={{ marginBottom: "12px" }}>
        <div className="skeleton" style={{ width: "120px", height: "10px" }} />
      </div>
      <div style={{ border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: "12px",
            padding: "10px 12px",
            borderBottom: i < 5 ? "1px solid var(--border)" : "none",
          }}>
            <div className="skeleton" style={{ width: "110px", height: "10px", flexShrink: 0 }} />
            <div className="skeleton" style={{ flex: 1, height: "13px" }} />
            <div className="skeleton" style={{ width: "60px", height: "22px", borderRadius: "8px", flexShrink: 0 }} />
            <div className="skeleton" style={{ flex: 1, height: "13px" }} />
          </div>
        ))}
      </div>

      <div style={{ marginTop: "32px", marginBottom: "12px" }}>
        <div className="skeleton" style={{ width: "140px", height: "10px" }} />
      </div>
      <div style={{ border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} style={{
            display: "flex", alignItems: "center", gap: "12px",
            padding: "10px 12px",
            borderBottom: i < 3 ? "1px solid var(--border)" : "none",
          }}>
            <div className="skeleton" style={{ width: "110px", height: "10px", flexShrink: 0 }} />
            <div className="skeleton" style={{ flex: 1, height: "13px" }} />
            <div className="skeleton" style={{ width: "30px", height: "10px", flexShrink: 0 }} />
            <div className="skeleton" style={{ flex: 1, height: "13px" }} />
          </div>
        ))}
      </div>
    </main>
  );
}