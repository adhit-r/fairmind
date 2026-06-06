// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://fairmind.xyz',
  base: '/',
  output: 'static',
  trailingSlash: 'ignore',
  vite: {
    optimizeDeps: {
      exclude: ['@resvg/resvg-js']
    },
    css: {
      postcss: './postcss.config.cjs'
    },
    build: {
      cssMinify: true,
      minify: true,
      target: 'esnext',
    }
  },
});
