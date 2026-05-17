/** @type {import('next').NextConfig} */
const nextConfig = {
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
