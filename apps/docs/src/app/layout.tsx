import type { ReactNode } from 'react';

export const metadata = {
  title: 'FairMind Docs',
  description: 'FairMind product documentation',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
