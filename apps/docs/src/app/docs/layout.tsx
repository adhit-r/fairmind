import { DocsLayout } from 'fumadocs-ui/layouts/notebook';
import type { ReactNode } from 'react';
import { baseOptions } from '../../lib/layout';
import { source } from '../../lib/source';

// The notebook layout: one header across the page (logo, search, links) over the menu and the page.
export default function Layout({ children }: { children: ReactNode }) {
  const base = baseOptions();
  return (
    <DocsLayout tree={source.pageTree} {...base} nav={{ ...base.nav, mode: 'top' }} sidebar={{ defaultOpenLevel: 0 }}>
      {children}
    </DocsLayout>
  );
}
