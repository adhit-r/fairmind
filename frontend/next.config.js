/** @type {import('next').NextConfig} */
const nextConfig = {
  // Development settings (remove static export for dev)
  // output: 'export', // Commented out for development
  trailingSlash: true,
  images: {
    unoptimized: true
  },
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development'
  },
  
  // Headers for security (only in production)
  async headers() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/(.*)',
          headers: [
            {
              key: 'X-Frame-Options',
              value: 'DENY'
            },
            {
              key: 'X-Content-Type-Options',
              value: 'nosniff'
            },
            {
              key: 'Referrer-Policy',
              value: 'origin-when-cross-origin'
            }
          ]
        }
      ];
    }
    return [];
  },
  
  // Redirects for production (only in production)
  async redirects() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/api/:path*',
          destination: 'https://api.fairmind.xyz/:path*',
          permanent: true
        }
      ];
    }
    return [];
  }
};

module.exports = nextConfig;
