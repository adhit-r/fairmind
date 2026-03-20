import { notFound } from "next/navigation";
import Link from "next/link";
import { DOC_ITEMS, readDocBySlug } from "../../../lib/docs";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export default async function DocPage({ params }: PageProps) {
  const { slug } = await params;
  const result = await readDocBySlug(slug);
  if (!result) notFound();

  return (
    <main style={{ maxWidth: 1200, margin: "20px auto", padding: "0 16px", fontFamily: "sans-serif" }}>
      <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 18 }}>
        <aside style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, height: "fit-content", position: "sticky", top: 14 }}>
          <p style={{ margin: "0 0 10px 0", fontWeight: 700 }}>Documentation</p>
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {DOC_ITEMS.map((item) => (
              <li key={item.slug} style={{ marginBottom: 8 }}>
                <Link href={`/docs/${item.slug}`} style={{ fontWeight: item.slug === slug ? 700 : 500 }}>
                  {item.title}
                </Link>
              </li>
            ))}
          </ul>
          <div style={{ marginTop: 14 }}>
            <Link href="/docs">Back to search</Link>
          </div>
        </aside>

        <article style={{ border: "1px solid #ddd", borderRadius: 8, padding: 18 }}>
          <h1 style={{ marginTop: 0 }}>{result.doc.title}</h1>
          <p style={{ color: "#555" }}>{result.doc.summary}</p>
          <pre style={{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", lineHeight: 1.45 }}>
            {result.content}
          </pre>
        </article>
      </div>
    </main>
  );
}

export function generateStaticParams() {
  return DOC_ITEMS.map((doc) => ({ slug: doc.slug }));
}
