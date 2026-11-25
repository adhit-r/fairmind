import { createMDX } from 'fumadocs-mdx/next';

const withMDX = createMDX();

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: new URL('../../', import.meta.url).pathname,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // Any page as raw MDX: /docs/get-started/quickstart.mdx
    return [{ source: '/docs/:path*.mdx', destination: '/llms.mdx/:path*' }];
  },
  async redirects() {
    const limits = '/docs/get-started/status-and-limits';
    // Order matters: the first match wins, so specific paths precede the folder patterns.
    return [
      ['/docs/getting-started', '/docs/get-started/quickstart'],
      ['/docs/quickstart', '/docs/get-started/quickstart'],
      ['/docs/limitations', limits],
      ['/docs/bias-detection', limits],
      ['/docs/simulation', limits],
      ['/docs/monitoring', limits],
      ['/docs/explainability', limits],
      ['/docs/model-provenance', '/docs/get-started/evidence-model'],
      ['/docs/security-compliance', '/docs'],
      ['/docs/concepts/capability-truth', limits],
      ['/docs/concepts/:slug', '/docs/get-started/:slug'],
      ['/docs/workflows/release-gate-in-ci', '/docs'],
      ['/docs/workflows/sdk-and-mcp', '/docs'],
      ['/docs/workflows/scheduled-monitoring', '/docs/app/release/monitoring'],
      ['/docs/workflows/operator-runbook', '/docs'],
      ['/docs/workflows/:slug', '/docs/journeys/:slug'],
      ['/docs/reference/:slug(deployment|configuration|authentication-rbac)', '/docs'],
      // The Self-host section was removed: the docs cover the product, not running it.
      ['/docs/self-host/:slug*', '/docs'],
      // Developer pages were removed: the docs cover using the app.
      ['/docs/build/:slug*', '/docs'],
      ['/docs/reference/api', '/docs'],
      ['/docs/reference/permissions-and-separation', '/docs/app/settings/settings'],
      ['/docs/journeys/scheduled-monitoring', '/docs/app/release/monitoring'],
      ['/docs/get-started/evidence-trust-review', '/docs/get-started/evidence-model'],
    ].map(([source, destination]) => ({ source, destination, permanent: true }));
  },
};

export default withMDX(nextConfig);
