import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/** Hand-maintained project entries shown on the home and projects pages. */
const projects = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/projects' }),
  schema: z.object({
    title: z.string(),
    blurb: z.string(),
    url: z.url().optional(),
    year: z.number(),
    order: z.number().default(50),
  }),
});

/** Dated blog posts, rendered at /blog and syndicated via /rss.xml. */
const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { projects, blog };
