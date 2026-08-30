import Link from "next/link";
import { searchDocs } from "../../lib/docs";

type PageProps = { searchParams?: Promise<{ q?: string }> };

export default async function DocsIndexPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const query = params.q?.trim() ?? "";
  const docs = await searchDocs(query);

  return (
    <main id="main-content" className="page-shell docs-index">
      <div className="index-heading">
        <h1>Find a P0 guide</h1>
        <p>Search verified release, integration, operating, and regulatory-context documentation.</p>
      </div>

      <form action="/docs" method="get" className="search-form" role="search">
        <label htmlFor="docs-search">Search documentation</label>
        <div className="search-row">
          <input id="docs-search" type="search" name="q" defaultValue={query} placeholder="Try evidence freshness or API integration" />
          <button type="submit">Search</button>
        </div>
      </form>

      <section className="search-results" aria-live="polite" aria-label="Documentation search results">
        <div className="result-summary">
          <strong>{docs.length} {docs.length === 1 ? "guide" : "guides"}</strong>
          {query && <span> matching “{query}”</span>}
        </div>
        {docs.length > 0 ? (
          <div className="result-rows">
            {docs.map((doc) => (
              <Link className="result-row" key={doc.slug} href={`/docs/${doc.slug}`}>
                <span className="result-section">{doc.section}</span>
                <span><strong>{doc.title}</strong><small>{doc.summary}</small></span>
                <span className="row-arrow" aria-hidden="true">Open</span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <h2>No guide matched</h2>
            <p>Try a broader term, or return to the complete guide list.</p>
            <Link className="button button-secondary" href="/docs">Clear search</Link>
          </div>
        )}
      </section>
    </main>
  );
}
