import type { MetadataRoute } from 'next';
import { getAllSkillNames } from '@/lib/data';

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://kalybratex.com'; // Update with actual domain

  // Get all skill names for dynamic routes
  const skillNames = getAllSkillNames();

  const skillPages = skillNames.map((name) => ({
    url: `${baseUrl}/skill/${name}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  return [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${baseUrl}/methodology`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.7,
    },
    ...skillPages,
  ];
}
