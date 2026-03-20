import Link from "next/link";
import { searchDocs } from "../../lib/docs";

type PageProps = {
  searchParams?: Promise<{ q?: string }>;
};

export default async function DocsIndexPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const query = params.q ?? "";
  const docs = await searchDocs(query);

  return (
    <main style={{ maxWidth: 1100, margin: "24px auto", padding: "0 16px", fontFamily: "sans-serif" }}>
      <h1>FairMind Docs</h1>
      <p>Navigate product workflows, governance features, and operational guides.</p>

      <form action="/docs" method="get" style={{ margin: "16px 0 24px 0" }}>
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder="Search docs..."
          style={{ width: "100%", maxWidth: 520, padding: "10px 12px", border: "1px solid #bbb", borderRadius: 6 }}
        />
      </form>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))", gap: 12 }}>
        {docs.map((doc) => (
          <Link
            key={doc.slug}
            href={`/docs/${doc.slug}`}
            style={{ border: "1px solid #ddd", borderRadius: 8, padding: 14, textDecoration: "none", color: "inherit" }}
          >
            <h3 style={{ margin: "0 0 6px 0" }}>{doc.title}</h3>
            <p style={{ margin: 0, color: "#444", fontSize: 14 }}>{doc.summary}</p>
          </Link>
        ))}
      </div>

      {docs.length === 0 && <p>No documents found for “{query}”.</p>}
    </main>
  );
}
