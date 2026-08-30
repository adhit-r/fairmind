import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { adjacentDocs, DOC_ITEMS, readDocBySlug } from "../../../lib/docs";

type PageProps = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const doc = DOC_ITEMS.find((item) => item.slug === slug);
  return doc ? { title: doc.title, description: doc.summary } : {};
}

export default async function DocPage({ params }: PageProps) {
  const { slug } = await params;
  const result = await readDocBySlug(slug);
  if (!result) notFound();
  const adjacent = adjacentDocs(slug);

  return (
    <main id="main-content" className="document-shell">
      <aside className="docs-sidebar" aria-label="Documentation navigation">
        <Link className="sidebar-home" href="/docs">All P0 guides</Link>
        <nav>
          {DOC_ITEMS.map((item) => (
            <Link
              aria-current={item.slug === slug ? "page" : undefined}
              className={item.slug === slug ? "active" : undefined}
              href={`/docs/${item.slug}`}
              key={item.slug}
            >
              <span>{item.title}</span>
              <small>{item.section}</small>
            </Link>
          ))}
        </nav>
      </aside>

      <article className="doc-article">
        <header className="doc-header">
          <span>{result.doc.section}</span>
          <h1>{result.doc.title}</h1>
          <p>{result.doc.summary}</p>
        </header>
        <div className="release-notice">
          <strong>P0 alpha documentation</strong>
          <span>These controls are internal and default-off unless an operator explicitly enables their full gate chain.</span>
        </div>
        <div className="markdown-body">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.content}</ReactMarkdown>
        </div>
        <nav className="doc-pagination" aria-label="Adjacent documentation">
          {adjacent.previous ? (
            <Link href={`/docs/${adjacent.previous.slug}`}><small>Previous</small><strong>{adjacent.previous.title}</strong></Link>
          ) : <span />}
          {adjacent.next && (
            <Link className="next" href={`/docs/${adjacent.next.slug}`}><small>Next</small><strong>{adjacent.next.title}</strong></Link>
          )}
        </nav>
      </article>
    </main>
  );
}

export function generateStaticParams() {
  return DOC_ITEMS.map((doc) => ({ slug: doc.slug }));
}
