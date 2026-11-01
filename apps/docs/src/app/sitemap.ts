import type { MetadataRoute } from 'next';
import { source } from '../lib/source';

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    { url: 'https://docs.fairmind.xyz', lastModified: now },
    ...source.getPages().map((page) => ({
      url: `https://docs.fairmind.xyz${page.url}`,
      lastModified: now,
    })),
  ];
}
