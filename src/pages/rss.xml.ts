import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';

/**
 * Renders the site's RSS feed from published blog posts.
 *
 * @param context - Astro endpoint context, used for the configured site URL.
 * @returns An RSS XML response listing every non-draft post, newest first.
 */
export async function GET(context: APIContext): Promise<Response> {
  const posts = await getCollection('blog', ({ data }) => !data.draft);

  return rss({
    title: 'Patrick Linton',
    description: 'Posts by Patrick Linton.',
    site: context.site ?? 'https://pashri.github.io',
    items: posts
      .sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf())
      .map((post) => ({
        title: post.data.title,
        description: post.data.description,
        pubDate: post.data.date,
        link: `/blog/${post.id}/`,
      })),
  });
}
