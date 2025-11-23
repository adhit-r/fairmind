// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://fairmind.xyz',
  base: '/',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [
    tailwind({
      // Tailwind configuration is automatically loaded from tailwind.config.js
      applyBaseStyles: true,
    }),
    sitemap(),
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
