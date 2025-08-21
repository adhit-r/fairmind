// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.fairmind.xyz',
  base: '/',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [
    tailwind({
      // Tailwind configuration is automatically loaded from tailwind.config.js
      applyBaseStyles: true,
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
});
