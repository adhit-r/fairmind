import type { Metadata } from 'next';
import { RootProvider } from 'fumadocs-ui/provider';
import type { ReactNode } from 'react';
import 'fumadocs-ui/style.css';
import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://docs.fairmind.xyz'),
  title: {
    default: 'FairMind Docs',
    template: '%s | FairMind Docs',
  },
  description: 'Build reviewable AI assurance evidence with FairMind.',
  applicationName: 'FairMind Docs',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'FairMind Docs',
    description: 'Bring your tests. Produce evidence you can defend.',
    url: 'https://docs.fairmind.xyz',
    siteName: 'FairMind Docs',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <RootProvider
          theme={{
            defaultTheme: 'light',
            enableSystem: false,
          }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
