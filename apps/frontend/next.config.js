/** @type {import('next').NextConfig} */
const nextConfig = {
  // Old routes from before the governance IA redesign. permanent:false so they can be retired later.
  async redirects() {
    return [
      { source: '/model-inventory', destination: '/systems', permanent: false },
      { source: '/onboard', destination: '/systems/new', permanent: false },
      { source: '/ai-governance', destination: '/systems', permanent: false },
      { source: '/compliance-dashboard', destination: '/frameworks', permanent: false },
      { source: '/compliance', destination: '/frameworks', permanent: false },
      { source: '/compliance/dashboard', destination: '/frameworks', permanent: false },
      { source: '/tests', destination: '/evaluations', permanent: false },
      { source: '/tests/:id', destination: '/evaluations/:id', permanent: false },
      { source: '/risks', destination: '/findings', permanent: false },
      { source: '/bias', destination: '/evaluations/fairness', permanent: false },
      { source: '/bias-simple', destination: '/evaluations/fairness', permanent: false },
      { source: '/advanced-bias', destination: '/evaluations/fairness', permanent: false },
      { source: '/multimodal-bias', destination: '/evaluations/fairness', permanent: false },
      { source: '/modern-bias', destination: '/evaluations/llm', permanent: false },
      { source: '/llm-judge', destination: '/evaluations/llm', permanent: false },
      { source: '/llm-testing', destination: '/evaluations/llm', permanent: false },
      { source: '/benchmarks', destination: '/evaluations/llm', permanent: false },
      { source: '/explainability-studio', destination: '/evaluations/explainability', permanent: false },
      { source: '/audit-reports', destination: '/reports', permanent: false },
      { source: '/fairness-documentation', destination: '/reports', permanent: false },
      { source: '/stakeholder-dashboard', destination: '/reports', permanent: false },
      { source: '/remediation-wizard', destination: '/remediation', permanent: false },
      { source: '/alerts', destination: '/monitoring?tab=alerts', permanent: false },
      { source: '/compliance-automation', destination: '/monitoring?tab=checks', permanent: false },
      { source: '/analytics', destination: '/monitoring', permanent: false },
      { source: '/realtime', destination: '/monitoring', permanent: false },
      { source: '/status', destination: '/settings?tab=status', permanent: false },
      { source: '/org-admin', destination: '/admin', permanent: false },
      { source: '/org-admin/members', destination: '/admin/members', permanent: false },
      { source: '/org-admin/roles', destination: '/admin/roles', permanent: false },
      { source: '/org-admin/settings', destination: '/admin/organization', permanent: false },
      { source: '/org-admin/audit-log', destination: '/admin/audit-log', permanent: false },
      { source: '/admin/users', destination: '/admin/members', permanent: false },
      { source: '/admin/registrations', destination: '/admin/access-requests', permanent: false },
      { source: '/model-dna', destination: '/systems', permanent: false },
      { source: '/provenance', destination: '/systems', permanent: false },
      { source: '/lifecycle', destination: '/systems', permanent: false },
      { source: '/ai-bom', destination: '/systems', permanent: false },
      { source: '/security', destination: '/evaluations', permanent: false },
      { source: '/marketplace', destination: '/dashboard', permanent: false },
      { source: '/marketplace/:id', destination: '/dashboard', permanent: false },
    ]
  },

  // Performance optimizations
  compress: true,
  
  // Image optimization
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Experimental features for better performance
  experimental: {
    optimizePackageImports: ['@tabler/icons-react', 'recharts'],
  },

  // Turbopack configuration (Next.js 16 default bundler)
  turbopack: {
    // jspdf's package.json resolves the `node` export condition during SSR
    // analysis, which loads `jspdf.node.min.js` and pulls in fflate's node
    // worker code that Turbopack cannot statically resolve. Force the browser
    // ES bundle for both client and server passes — jspdf is only ever
    // invoked from `'use client'` event handlers (e.g. audit-reports/page.tsx),
    // so the SSR pre-pass never actually executes the code.
    resolveAlias: {
      jspdf: 'jspdf/dist/jspdf.es.min.js',
    },
  },

  // Webpack optimizations (kept for compatibility but Turbopack is preferred)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Tree shaking optimizations (removed usedExports due to conflict with cacheUnaffected)
      config.optimization = {
        ...config.optimization,
        sideEffects: false,
      }
    }
    return config
  },

  // Production optimizations
  productionBrowserSourceMaps: false,
  
  // Output configuration
  output: 'standalone',
}

module.exports = nextConfig
