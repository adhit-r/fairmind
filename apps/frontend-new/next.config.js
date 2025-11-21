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

        // Webpack optimizations
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
