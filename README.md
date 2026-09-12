# pashri.github.io

Personal site, built with Astro and Tailwind, deployed to GitHub Pages by
GitHub Actions on every push to `main`.

## Running locally

```sh
npm install
npm run dev
```

## Adding content

Projects are Markdown files in `src/content/projects/`; the `order` field
controls their position and the three lowest appear on the home page.
Posts are Markdown files in `src/content/blog/` and are hidden while
`draft: true`.

## Hosting web apps alongside this

Apps live in their own repositories with their own Pages deployment,
served at `pashri.github.io/<repo>`. Their build must set the base path to
`/<repo>/` or every asset request 404s.
