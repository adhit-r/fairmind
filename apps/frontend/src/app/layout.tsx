import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { MantineAppProvider } from '@/providers/mantine-provider';
import { AppShell } from '@/components/layout/AppShell';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'FairMind - Ethical AI Governance Platform',
  description: 'AI governance, bias detection, and compliance platform for responsible AI development',
  keywords: 'AI governance, ethical AI, bias detection, fairness, machine learning',
  authors: [{ name: 'FairMind Team' }],
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <MantineAppProvider>
          <AppShell>
              {children}
          </AppShell>
        </MantineAppProvider>
      </body>
    </html>
  );
}
