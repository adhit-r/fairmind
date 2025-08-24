// Production Deployment Configuration
module.exports = {
  // API Configuration
  api: {
    baseUrl: 'https://api.fairmind.xyz',
    timeout: 30000,
    retries: 3
  },
  
  // App Configuration
  app: {
    url: 'https://app-demo.fairmind.xyz',
    environment: 'production',
    version: '1.0.0'
  },
  
  // Build Configuration
  build: {
    output: 'export',
    trailingSlash: true,
    images: {
      unoptimized: true
    }
  },
  
  // Environment Variables
  env: {
    NEXT_PUBLIC_API_URL: 'https://api.fairmind.xyz',
    NEXT_PUBLIC_APP_URL: 'https://app-demo.fairmind.xyz',
    NEXT_PUBLIC_ENVIRONMENT: 'production'
  }
};
