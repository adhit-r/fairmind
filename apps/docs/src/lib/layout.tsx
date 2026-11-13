import type { BaseLayoutProps } from 'fumadocs-ui/layouts/shared';

export function baseOptions(): BaseLayoutProps {
  return {
    nav: {
      title: (
        <span className="docs-brand">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/logo-mark.svg" alt="" width={28} height={28} />
          <span>FairMind</span>
          <span className="docs-brand-pill">Docs</span>
        </span>
      ),
    },
    links: [
      { text: 'Website', url: 'https://fairmind.xyz', external: true },
      { type: 'button', text: 'Try the demo', url: 'https://app.fairmind.xyz/login', external: true },
    ],
    githubUrl: 'https://github.com/adhit-r/fairmind',
  };
}
