const DOC_PAGES: Array<{ slug: string; title: string }> = [
  { slug: "getting-started", title: "Getting Started" },
  { slug: "bias-detection", title: "Bias Detection" },
  { slug: "simulation", title: "Simulation" },
  { slug: "monitoring", title: "Monitoring" },
  { slug: "model-provenance", title: "Model Provenance" },
  { slug: "explainability", title: "Explainability" },
  { slug: "security-compliance", title: "Security & Compliance" },
];

export default async function DocsHome() {
  return (
    <main style={{ maxWidth: 1100, margin: "32px auto", fontFamily: "sans-serif", padding: "0 16px" }}>
      <h1>FairMind Documentation</h1>
      <p>Product workflow guide for AI governance, risk management, and audit readiness.</p>
      <p>
        Main website: <a href="https://fairmind.xyz">fairmind.xyz</a> | App: <a href="https://app.fairmind.xyz">app.fairmind.xyz</a>
      </p>
      <p>
        Browse full docs: <a href="/docs">/docs</a>
      </p>

      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, marginTop: 20 }}>
        <h2 style={{ marginTop: 0 }}>How Teams Use FairMind</h2>
        <ol>
          <li>Select AI system scope and owners.</li>
          <li>Run bias, explainability, and security/compliance checks.</li>
          <li>Review blockers and recommended remediations.</li>
          <li>Track runtime monitoring and alerts.</li>
          <li>Generate audit-ready evidence and reports.</li>
        </ol>
      </section>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 20 }}>
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>Core Features</h3>
          <ul>
            <li>Bias and fairness analysis across model lifecycles.</li>
            <li>Compliance tracking and evidence workflows.</li>
            <li>Monitoring, alerts, and operational governance.</li>
            <li>Model provenance and explainability artifacts.</li>
          </ul>
        </section>
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>What Makes FairMind Novel</h3>
          <ul>
            <li>Decision-first governance flows, not only metrics dashboards.</li>
            <li>Unified view for engineering, compliance, and operations teams.</li>
            <li>Evidence-backed readiness for audits and release gates.</li>
          </ul>
        </section>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>Use Cases</h3>
          <ul>
            <li>Pre-release AI risk review and sign-off.</li>
            <li>Continuous model compliance monitoring in production.</li>
            <li>Regulatory and internal audit preparation.</li>
            <li>Cross-country fairness and localization checks.</li>
          </ul>
        </section>
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h3 style={{ marginTop: 0 }}>Roadmap (Product)</h3>
          <ul>
            <li>Workflow-centric orchestration and next-best-actions.</li>
            <li>Role-based workspaces for compliance, ML, and leadership.</li>
            <li>Expanded incident management and remediation SLAs.</li>
            <li>Stronger enterprise assurance and audit pack automation.</li>
          </ul>
        </section>
      </div>

      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, marginTop: 20 }}>
        <h3 style={{ marginTop: 0 }}>Documentation Sections</h3>
        <ul style={{ columns: 2 }}>
          {DOC_PAGES.map((p) => (
            <li key={p.slug}>
              <a href={`/docs/${p.slug}`}>{p.title}</a>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
