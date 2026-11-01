import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: new URL('../../', import.meta.url).pathname,
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      { source: '/docs/getting-started', destination: '/docs/quickstart', permanent: true },
      { source: '/docs/bias-detection', destination: '/docs/concepts/capability-truth', permanent: true },
      { source: '/docs/simulation', destination: '/docs/concepts/capability-truth', permanent: true },
      { source: '/docs/monitoring', destination: '/docs/limitations', permanent: true },
      { source: '/docs/model-provenance', destination: '/docs/concepts/evidence-model', permanent: true },
      { source: '/docs/explainability', destination: '/docs/concepts/capability-truth', permanent: true },
      { source: '/docs/security-compliance', destination: '/docs/reference/authentication-rbac', permanent: true },
    ];
  },
};

export default withMDX(nextConfig);
