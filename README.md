# pashri.github.io

Patrick Linton · Notes: short posts on transport, housing, and climate, with the occasional software and data post. Built with [Pelican](https://getpelican.com) and published to GitHub Pages at https://pashri.github.io.

## One-time setup

```sh
uv sync
uv run playwright install chromium   # draws the link-preview cards
```

## Writing a post

Create a Markdown file in `content/posts/`. The filename can be anything (`parking-minimums.md`); readers never see it.

Start the file with this header, then a blank line, then the post:

```
Title: Parking minimums are a housing tax
Date: 2026-10-20
Tags: Housing, Transport, Sydney

The first paragraph starts here.
```

`Ref:` is left out on purpose. It's added when you publish (see below).

Optional header lines, added above the blank line only when you need them:

| Line | What it does |
|---|---|
| `Summary: One sentence.` | The description shown in link previews. Without it, the first paragraph is used. |
| `Series: Recording every Sydney bus` | Adds the post to that series (see [Series](#series)). |
| `Image: chart.png` | The picture in the link-preview card (see [Images](#images)). |

### Tags

Use at least one subject, plus any places. Only these tags are allowed, and any other tag fails the build. To add one, see [Adding a tag](#adding-a-tag).

| Subjects | Places |
|---|---|
| Transport | Sydney |
| Housing | Cambridge |
| Placemaking | New York |
| Climate | |
| Software & data | |

Write them exactly as above, capitals included. The order doesn't matter.

### Footnotes

```
Women cyclists are killed more often.[^study] Here's another claim.[^2]

[^study]: Author et al. (2025). Title. https://doi.org/10.xxxx/xxxxx
[^2]: Any text, with [links](https://example.com).
```

Notes appear at the bottom of the post. On a computer, hovering over a footnote number shows the note.

### Images

Put images in a folder next to the post, with the same name as the post's file:

```
content/posts/parking-minimums.md
content/posts/parking-minimums/chart.png
```

An image on a line of its own becomes a figure, with its quoted title as the caption:

```
![Bar chart of parking spaces per flat](chart.png "Figure 1. Parking required per new flat.")
```

The `Image:` header line only sets the picture inside the link-preview card. To show that image in the post as well, add it to the text like above.

### Series

Give every post in the series the same `Series:` line. Parts are ordered by date. To order them by hand instead, add `Series_index: 1`, `2` and so on to *every* part. Setting it on only some parts puts those parts first.

Each part shows a box listing the whole series, and the series appears at `/series/`.

### Interactive figures (embeds)

Put a script and its data in the post's folder, then add one line on its own:

```
{% embed src="route-league.js" data="route-league.json" caption="Figure 2. On-time share by route." %}
```

The script is an ES module whose default export draws into the page:

```js
export default async function (mount, dataUrl) {
  const data = await (await fetch(dataUrl)).json();
  mount.textContent = `${data.length} routes`;   // draw the chart here
}
```

RSS readers can't run the script, so they show a link to the post instead.

### Code

Fenced code blocks with a language are coloured:

````
```sql
SELECT route_id, avg(on_time) FROM mart_trip GROUP BY route_id;
```
````

### Headings, quotes, tables, lists

Standard Markdown. Each prose paragraph is numbered automatically. Headings, lists, quotes, code, tables and figures aren't.

## Previewing

```sh
uv run preview
```

Open http://localhost:8000. The site rebuilds every time you save.

- A post without a `Ref:` is listed under **Not yet published** at the top of the home page.
- Mistakes such as a misspelt tag are printed in the terminal. Preview keeps running, but the same mistake would stop the live site from building.

## Publishing

Anything committed to `main` goes live, so **don't commit a post until it's finished.** Unfinished posts stay as uncommitted files on your laptop.

```sh
uv run publish content/posts/parking-minimums.md
git add content/posts/parking-minimums*
git commit -m "Publish: Parking minimums are a housing tax"
git push
```

`publish` adds the next free reference (`Ref: 26/015`) and sets `Date:` to today. The post goes live at https://pashri.github.io/26/015/ about two minutes after the push.

### From a phone

On github.com, open `content/posts/`, choose **Add file → Create new file**, and write the whole post, including these two lines:

```
Ref: 26/015
Date: 2026-10-20
```

Use the number after the highest `Ref:` for this year in `content/posts/` (hidden posts count too). If you get it wrong, the build fails with a clear message and nothing goes live. Every save on GitHub is a commit, and every commit goes live, so only do this with a finished post.

## References

Every post has a permanent reference, `YY/NNN`: the year, then a number that starts at 001 each January. The reference is also the post's address (`/26/015/`), so **never change a reference once it's published.**

The build stops, and nothing goes live, if:

| Message | Fix |
|---|---|
| `missing Ref` | Run `uv run publish` on the file, or add `Ref:` by hand. |
| `malformed Ref '26-15'` | Use `YY/NNN`, e.g. `26/015`. |
| `Ref 26/015 is used by a.md and b.md` | Give the newer post the next free number. |
| `Ref 25/003 doesn't match Date 2026-01-02` | The year in the reference must match the year in `Date:`. |
| `gap in 2026: 26/014 is missing` | Each year must run 001, 002, 003… with nothing skipped. A gap usually means a post was deleted (see below) or numbered by hand. |
| `unknown tag 'transport'` | Use a tag from the lists in `pelicanconf.py`, spelt exactly, or [add a new one](#adding-a-tag). |
| `no subject tag` | Add at least one subject tag, e.g. Transport. |
| `Image 'chart.png' not found in parking-minimums/` | Put the file in the post's folder, or fix the name on the `Image:` line. |

## Changing or removing a published post

Edit the file and push. Keep `Ref:` the same.

To take a post down, don't delete it, because that leaves a gap in the numbering. Add `Status: hidden` instead. The post disappears from the site, but its number stays reserved.

## Adding a tag

The tags are two lists in `pelicanconf.py`:

```python
SUBJECT_TAGS = ["Transport", "Housing", "Placemaking", "Climate", "Software & data"]
PLACE_TAGS = ["Sydney", "Cambridge", "New York"]
```

Add the new tag to the right list, in the position you want it to appear, then use it in a post and push. The tag bar under the masthead, the order tags are shown on each post, and the build check all come from these lists. The tag's page appears by itself at `/tags/<tag-in-lowercase-with-hyphens>/`, e.g. "Public health" becomes `/tags/public-health/`.

Renaming a tag changes its page's address, and every post using the old name fails the build until you update it. Removing a tag works the same way.

## Other pages

- **About:** `content/pages/about.md`.
- **Sample posts:** the three lorem ipsum posts (`content/posts/sample-*.md` and their folders) exist to show every feature. Delete all three together; deleting only some can leave a gap in 2025, which fails the build.

## Theme

- **Colours and fonts:** the variables at the top of `theme/static/css/site.css`, with light and dark versions. Dark mode follows the reader's device setting.
- **Page layouts:** `theme/templates/`.
- **Link-preview card design:** `theme/templates/card.html`.
- **Fonts:** self-hosted in `theme/static/fonts/` (Newsreader, Source Sans 3, Source Code Pro; SIL Open Font License).

## Deploying

Every push to `main` runs `.github/workflows/deploy.yml`, which builds the site and publishes it to GitHub Pages.

If the site doesn't update, go to **github.com/pashri/pashri.github.io → Actions** and open the run with a red ✗. The log lists every problem, usually the reference errors above.

## Visitor numbers

The site counts visitors with GoatCounter, which uses no cookies. See the numbers at https://pashri.goatcounter.com. The code that connects the site to that dashboard is `GOATCOUNTER_CODE` in `publishconf.py`; set it to `""` to switch counting off.
