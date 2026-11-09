import Link from 'next/link';

const CAPABILITIES = [
  ['Environmental evaluation', 'Validated evidence path'],
  ['Evidence workbench', 'Implemented with review boundaries'],
  ['Remediation and retest', 'Implemented'],
  ['LLM judge', 'External-provider dependent'],
];

export default function HomePage() {
  return (
    <main className="home-shell">
      <header className="home-nav" aria-label="Primary navigation">
        <Link className="wordmark" href="/">
          <span className="wordmark-mark" aria-hidden="true">FM</span>
          <span>FairMind Docs</span>
        </Link>
        <nav>
          <Link href="/docs">Documentation</Link>
          <a href="https://app.fairmind.xyz">Open product</a>
          <a href="https://github.com/adhit-r/fairmind">GitHub</a>
        </nav>
      </header>

      <section className="home-hero">
        <p className="eyebrow">AI assurance evidence workbench</p>
        <h1>Bring your tests.<br />Produce evidence you can defend.</h1>
        <p className="hero-copy">
          FairMind connects AI systems, evaluations, evidence, controls, remediation, and human decisions without turning a test result into a compliance claim.
        </p>
        <div className="hero-actions">
          <Link className="button button-primary" href="/docs/get-started/quickstart">Start the quickstart</Link>
          <Link className="button button-secondary" href="/docs">Understand the model</Link>
        </div>
      </section>

      <section className="ledger-strip" aria-label="Assurance workflow">
        {['Scope the system', 'Run a supported test', 'Review the evidence', 'Close the loop'].map((label, index) => (
          <div className="ledger-step" key={label}>
            <span>0{index + 1}</span>
            <strong>{label}</strong>
          </div>
        ))}
      </section>

      <section className="home-section split-section">
        <div>
          <p className="eyebrow">Capability truth</p>
          <h2>Know what the product can prove.</h2>
          <p>
            Every evaluator is described by its actual evidence boundary: validated, metadata-only, external-provider, interface-only, unavailable, or research-only.
          </p>
          <Link className="text-link" href="/docs/get-started/status-and-limits">Read the capability model</Link>
        </div>
        <div className="capability-ledger">
          {CAPABILITIES.map(([name, status]) => (
            <div className="capability-row" key={name}>
              <strong>{name}</strong>
              <span>{status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="home-section final-cta">
        <p className="eyebrow">First useful outcome</p>
        <h2>Register one system. Record one defensible artifact.</h2>
        <p>The quickstart takes you from local setup to an evidence record with an explicit reviewer boundary.</p>
        <Link className="button button-primary" href="/docs/get-started/quickstart">Open quickstart</Link>
      </section>
    </main>
  );
}
