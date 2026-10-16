"""Write a page for each Series and an index of all Series."""

from pelican import signals
from pelican.contents import Article
from pelican.generators import ArticlesGenerator, Generator
from pelican.utils import slugify
from pelican.writers import Writer


def series_slug(name: str, settings: dict) -> str:
    """Turn a Series name into the slug used in its URL.

    Parameters
    ----------
    name : str
        The Series name as written in Posts.
    settings : dict
        Pelican settings holding SLUG_REGEX_SUBSTITUTIONS.

    Returns
    -------
    str
        The slug, e.g. ``recording-every-sydney-bus``.
    """
    return slugify(name, regex_subs=settings["SLUG_REGEX_SUBSTITUTIONS"])


def visible_parts(parts: list[Article], preview: bool) -> list[Article]:
    """Keep the parts a reader should see.

    Parameters
    ----------
    parts : list[Article]
        Every part pelican-series found, hidden Posts included.
    preview : bool
        True in the preview build, where unpublished Posts are shown.

    Returns
    -------
    list[Article]
        Published parts, plus unpublished ones in preview.
    """
    return [part for part in parts if part.status == "published"
            and (preview or not getattr(part, "unpublished", False))]


def annotate(generators: list[Generator]) -> None:
    """Give every Post in a Series the URL of its Series page.

    Parameters
    ----------
    generators : list[Generator]
        All of Pelican's generators.
    """
    for generator in generators:
        if not isinstance(generator, ArticlesGenerator):
            continue
        for post in generator.articles + generator.hidden_articles:
            if getattr(post, "series", None):
                post.series_url = (
                    f"series/{series_slug(post.series['name'], generator.settings)}/")


def write(generator: ArticlesGenerator, writer: Writer) -> None:
    """Write each Series page and the index of all Series.

    Parameters
    ----------
    generator : ArticlesGenerator
        Pelican's article generator.
    writer : Writer
        The writer used for every other page.
    """
    preview = generator.settings["PREVIEW"]
    shelves = [(name, series_slug(name, generator.settings),
                visible_parts(parts, preview))
               for name, parts in
               sorted(generator.context["article_series"].items())]
    shelves = [shelf for shelf in shelves if shelf[2]]
    for name, slug, parts in shelves:
        writer.write_file(
            f"series/{slug}/index.html", generator.get_template("series"),
            generator.context, series_name=name, parts=parts,
            page_url=f"series/{slug}/")
    writer.write_file(
        "series/index.html", generator.get_template("series_index"),
        generator.context, shelves=shelves, url="series/")


def register() -> None:
    """Connect the plugin to Pelican's signals."""
    signals.all_generators_finalized.connect(annotate)
    signals.article_writer_finalized.connect(write)
