// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import image from '@astrojs/image';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.fairmind.xyz',
  base: '/',
  output: 'static',
  trailingSlash: 'ignore',
  build: {
    format: 'file',
    inlineStylesheets: 'auto',
    assets: '_assets',
  },
  integrations: [
    tailwind({
      // Tailwind configuration is automatically loaded from tailwind.config.js
      applyBaseStyles: true,
    }),
    image({
      serviceEntryPoint: '@astrojs/image/sharp',
    }),
  ],
  vite: {
    optimizeDeps: {
      exclude: ['@resvg/resvg-js']
    },
    css: {
      postcss: './postcss.config.js'
    },
    build: {
      cssMinify: true,
      minify: true,
      target: 'esnext',
    }
  },
  // Enable prefetch for better performance
  prefetch: {
    prefetchAll: true,
  },
});
