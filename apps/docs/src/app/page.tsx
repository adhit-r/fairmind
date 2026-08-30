import Link from "next/link";
import { DOC_ITEMS } from "../lib/docs";

const sections = ["Start here", "Assurance foundation", "Operate safely", "Regulatory context"] as const;

export default function DocsHome() {
  return (
    <main id="main-content" className="page-shell home-shell">
      <section className="home-intro" aria-labelledby="home-title">
        <div>
          <h1 id="home-title">Evidence you can trace.<br />Claims you can defend.</h1>
          <p className="lede">
            The P0 release establishes FairMind&apos;s internal assurance control-plane foundation: exact scope,
            signed evidence admission, operational freshness, review separation, and append-only decisions.
          </p>
          <div className="home-actions">
            <Link className="button button-primary" href="/docs/getting-started">Start locally</Link>
            <Link className="button button-secondary" href="/docs/release-boundary">Read the release boundary</Link>
          </div>
        </div>
        <aside className="truth-panel" aria-label="Release truth">
          <h2>What this alpha is</h2>
          <dl>
            <div><dt>Control plane</dt><dd>P0 complete</dd></div>
            <div><dt>Exposure</dt><dd>Internal, gated</dd></div>
            <div><dt>Evaluator workers</dt><dd>Unavailable</dd></div>
            <div><dt>Compliance verdict</dt><dd>Not provided</dd></div>
          </dl>
        </aside>
      </section>

      <section className="boundary-callout" aria-labelledby="boundary-title">
        <h2 id="boundary-title">The boundary is part of the product</h2>
        <p>
          A prepared run is not an executed evaluation. A verified artifact is not an approved governance
          decision. A framework crosswalk is not legal advice or conformity evidence.
        </p>
      </section>

      <section className="guide-index" aria-labelledby="guide-title">
        <div className="section-heading">
          <h2 id="guide-title">P0 operating manual</h2>
          <Link href="/docs">Search all guides</Link>
        </div>
        {sections.map((section) => (
          <div className="guide-group" key={section}>
            <h3>{section}</h3>
            <div className="guide-rows">
              {DOC_ITEMS.filter((item) => item.section === section).map((item) => (
                <Link className="guide-row" href={`/docs/${item.slug}`} key={item.slug}>
                  <span><strong>{item.title}</strong><small>{item.summary}</small></span>
                  <span aria-hidden="true" className="row-arrow">View</span>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
