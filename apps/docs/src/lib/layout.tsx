import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <span className="docs-brand">
          <span className="docs-brand-mark">FM</span>
          <span>FairMind Docs</span>
        </span>
      ),
      transparentMode: 'top',
    },
    links: [
      { text: 'Product', url: 'https://app.fairmind.xyz', external: true },
      { text: 'Website', url: 'https://fairmind.xyz', external: true },
    ],
    githubUrl: 'https://github.com/adhit-r/fairmind',
  };
}
