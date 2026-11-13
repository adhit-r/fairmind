import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <span className="docs-brand">
          <span className="docs-brand-mark" aria-hidden="true" />
          <span>FairMind</span>
        </span>
      ),
      transparentMode: 'top',
    },
    links: [
      { text: 'Try the demo', url: 'https://app.fairmind.xyz/login', external: true },
      { text: 'Website', url: 'https://fairmind.xyz', external: true },
    ],
    githubUrl: 'https://github.com/adhit-r/fairmind',
  };
}
