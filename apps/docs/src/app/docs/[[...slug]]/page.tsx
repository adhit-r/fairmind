import { notFound } from 'next/navigation';
import defaultMdxComponents from 'fumadocs-ui/mdx';
import { Step, Steps } from 'fumadocs-ui/components/steps';
import { Tab, Tabs } from 'fumadocs-ui/components/tabs';
import { DocsBody, DocsDescription, DocsPage, DocsTitle } from 'fumadocs-ui/page';
import type { Metadata } from 'next';
import { Status } from '../../../components/status';
import { Access } from '../../../components/access';
import { PageAnatomy } from '../../../components/page-anatomy';
import { TryIt } from '../../../components/try-it';
import { Watch } from '../../../components/watch';
import { TourSteps } from '../../../components/tour-steps';
import { DemoStrip, HomeHero } from '../../../components/home';
import { source } from '../../../lib/source';

type PageProps = {
  params: Promise<{ slug?: string[] }>;
};

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const page = source.getPage(slug);
  if (!page) notFound();

  const MDX = page.data.body;

  return (
    <DocsPage
      toc={page.data.toc}
      tableOfContent={{
        style: 'clerk',
        footer: (
          <div className="fm-rail">
            <a className="pill" href="https://app.fairmind.xyz/login">Open the demo ↗</a>
            <a className="pill" href={`${page.url === '/docs' ? '/docs/index' : page.url}.mdx`}>View as Markdown</a>
          </div>
        ),
      }}
      editOnGithub={{
        owner: 'adhit-r',
        repo: 'fairmind',
        sha: 'main',
        path: `apps/docs/content/docs/${page.file.path}`,
      }}
    >
      {/* The front page opens with its own hero instead of the title block. */}
      {page.url !== '/docs' && (
        <>
          <DocsTitle>{page.data.title}</DocsTitle>
          <DocsDescription>{page.data.description}</DocsDescription>
        </>
      )}
      <DocsBody>
        <MDX components={{ ...defaultMdxComponents, Step, Steps, Tab, Tabs, Status, Access, PageAnatomy, Watch, TryIt, TourSteps, HomeHero, DemoStrip }} />
      </DocsBody>
      <footer className="fm-footer">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <span><img src="/logo-mark.svg" alt="" width={18} height={18} /> FairMind · AGPL-3.0</span>
        <a href="https://github.com/adhit-r/fairmind">GitHub</a>
      </footer>
    </DocsPage>
  );
}

export function generateStaticParams() {
  return source.generateParams();
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = source.getPage(slug);
  if (!page) notFound();

  return {
    title: page.data.title,
    description: page.data.description,
    alternates: { canonical: page.url },
  };
}
