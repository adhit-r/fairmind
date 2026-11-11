/** @type {import('next').NextConfig} */
// Sent on every page and proxied API response. Cloudflare can add the same at
// the edge (deploy/lightsail/cloudflare.md); setting them here keeps them when
// the app runs anywhere else. A full CSP with nonces is a separate change.
const SECURITY_HEADERS = [
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Content-Security-Policy', value: "frame-ancestors 'none'" },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'geolocation=(), microphone=(), camera=()' },
]

const nextConfig = {
  poweredByHeader: false,

  async headers() {
    return [
      { source: '/:path*', headers: SECURITY_HEADERS },
      // Authenticated API answers must never sit in a shared cache.
      { source: '/api/:path*', headers: [{ key: 'Cache-Control', value: 'no-store' }] },
    ]
  },

  async redirects() {
    return [
      {
        source: '/audit-reports',
        destination: '/reports?view=builder',
        permanent: false,
      },
      {
        source: '/compliance/dashboard',
        destination: '/compliance-dashboard',
        permanent: false,
      },
      // Older addresses for pages that now live in the new menu.
      { source: '/integrations', destination: '/discovery', permanent: false },
      { source: '/model-inventory', destination: '/systems', permanent: false },
      { source: '/risks', destination: '/findings', permanent: false },
      { source: '/remediation', destination: '/findings', permanent: false },
      { source: '/compliance/runs', destination: '/runs', permanent: false },
      { source: '/compliance/evaluations', destination: '/evaluations', permanent: false },
      { source: '/evidence/packs', destination: '/auditor-packs', permanent: false },
      { source: '/org-admin/settings', destination: '/settings', permanent: false },
      {
        source: '/remediation-wizard',
        destination: '/remediation?mode=guided',
        permanent: false,
      },
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
    // invoked from `'use client'` event handlers (e.g. reports/components/AssuranceReportStudio.tsx),
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

const { withAstryx } = require('@astryxdesign/build/next')

module.exports = withAstryx(nextConfig)
