"""Markdown additions: embed lines, image figures and attachment links."""

import html
import re
import shutil
import xml.etree.ElementTree as etree
from pathlib import Path
from typing import Final

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from pelican import Pelican, signals
from pelican.contents import Article
from pelican.generators import ArticlesGenerator

EMBED_LINE: Final[re.Pattern[str]] = re.compile(
    r"\{%\s*embed\s+(?P<attrs>.*?)\s*%\}")
EMBED_ATTR: Final[re.Pattern[str]] = re.compile(r'(\w+)="([^"]*)"')
RELATIVE_LINK: Final[re.Pattern[str]] = re.compile(
    r'\b(src|href|data-src|data-data)="(?![a-z]+:|/|#)([^"]+)"')
POST_URL_TOKEN: Final[str] = "__POST_URL__"


def embed_html(attrs: dict[str, str]) -> str:
    """Build the figure markup for one embed line.

    Parameters
    ----------
    attrs : dict[str, str]
        The ``src``, ``data`` and optional ``caption`` attributes.

    Returns
    -------
    str
        A ``<figure class="embed">`` element as HTML.

    Raises
    ------
    ValueError
        If ``src`` or ``data`` is missing.
    """
    missing = sorted({"src", "data"} - attrs.keys())
    if missing:
        raise ValueError(f"embed is missing {', '.join(missing)}")
    caption = attrs.get("caption", "")
    figcaption = (f"<figcaption>{html.escape(caption)}</figcaption>"
                  if caption else "")
    return (f'<figure class="embed" data-src="{html.escape(attrs["src"])}"'
            f' data-data="{html.escape(attrs["data"])}">'
            '<div class="embed-mount"></div>'
            f'<p class="embed-fallback"><a href="{POST_URL_TOKEN}">'
            "Interactive figure: view it on the site</a></p>"
            f"{figcaption}</figure>")


class EmbedPreprocessor(Preprocessor):
    """Replace ``{% embed ... %}`` lines with figure markup."""

    def run(self, lines: list[str]) -> list[str]:
        """Convert every embed line, leaving other lines alone.

        Parameters
        ----------
        lines : list[str]
            The Markdown source, one line per item.

        Returns
        -------
        list[str]
            The lines, with each embed line replaced by a stash placeholder.
        """
        return [self.convert(line=line) for line in lines]

    def convert(self, line: str) -> str:
        """Convert one line if it is an embed line.

        Parameters
        ----------
        line : str
            One line of Markdown.

        Returns
        -------
        str
            The line itself, or a placeholder for the stored figure.
        """
        match = EMBED_LINE.fullmatch(line.strip())
        if match is None:
            return line
        attrs = dict(EMBED_ATTR.findall(match["attrs"]))
        return self.md.htmlStash.store(embed_html(attrs=attrs))


class FigureTreeprocessor(Treeprocessor):  # pylint: disable=too-few-public-methods
    """Turn a paragraph holding only an image into a figure."""

    def run(self, root: etree.Element) -> None:
        """Convert every lone-image paragraph under ``root``.

        Parameters
        ----------
        root : etree.Element
            The parsed document.
        """
        for para in list(root.iter("p")):
            if is_lone_image(para=para):
                to_figure(para=para)


def is_lone_image(para: etree.Element) -> bool:
    """Say whether a paragraph contains one image and nothing else.

    Parameters
    ----------
    para : etree.Element
        A ``<p>`` element.

    Returns
    -------
    bool
        True if the only content is a single ``<img>``.
    """
    return (len(para) == 1 and para[0].tag == "img"
            and not (para.text or "").strip()
            and not (para[0].tail or "").strip())


def to_figure(para: etree.Element) -> None:
    """Rewrite a lone-image paragraph as ``<figure>`` with a caption.

    Parameters
    ----------
    para : etree.Element
        A ``<p>`` holding one ``<img>``; its title becomes the caption.
    """
    para.tag = "figure"
    title = para[0].attrib.pop("title", "")
    if title:
        caption = etree.SubElement(para, "figcaption")
        caption.text = title


class NotesExtension(Extension):
    """Register the embed preprocessor and the figure treeprocessor."""

    def extendMarkdown(self, md: Markdown) -> None:  # noqa: N802
        """Add both processors to a Markdown instance.

        Parameters
        ----------
        md : Markdown
            The Markdown instance Pelican's reader uses.
        """
        md.preprocessors.register(EmbedPreprocessor(md), "notes_embed", 25)
        md.treeprocessors.register(
            FigureTreeprocessor(md), "notes_figure", 15)


def add_extension(pelican: Pelican) -> None:
    """Add the extension to Pelican's Markdown settings.

    Parameters
    ----------
    pelican : Pelican
        The Pelican instance being initialised.
    """
    pelican.settings["MARKDOWN"].setdefault("extensions", []).append(
        NotesExtension())


def rewrite_links(generator: ArticlesGenerator) -> None:
    """Rewrite each Post's relative links and copy its attachments.

    Parameters
    ----------
    generator : ArticlesGenerator
        Pelican's article generator, after every Post has its URL.
    """
    site_url = generator.settings["SITEURL"]
    for post in generator.articles:
        rewrite_post(post=post, site_url=site_url)
        copy_attachments(post=post, output=Path(generator.output_path))


def copy_attachments(post: Article, output: Path) -> None:
    """Copy a Post's attachment folder next to its page.

    Hidden Posts are never passed in, so their attachments stay unpublished.

    Parameters
    ----------
    post : Article
        A Post whose attachments sit in a same-named folder beside it.
    output : Path
        The build's output folder.
    """
    folder = Path(post.source_path).with_suffix("")
    if folder.is_dir():
        shutil.copytree(folder, output / Path(post.save_as).parent,
                        dirs_exist_ok=True)


def rewrite_post(post: Article, site_url: str) -> None:
    """Point one Post's relative links at its own address.

    Parameters
    ----------
    post : Article
        The Post to rewrite.
    site_url : str
        The site's base URL; empty in the preview build.
    """
    base = f"{site_url}/{post.url}"
    content = RELATIVE_LINK.sub(
        lambda match: f'{match[1]}="{base}{match[2]}"',
        post._content,  # pylint: disable=protected-access
    )
    post._content = content.replace(  # pylint: disable=protected-access
        POST_URL_TOKEN, f"{site_url}/{post.url}")


def register() -> None:
    """Connect the plugin to Pelican's signals."""
    signals.initialized.connect(add_extension)
    signals.article_generator_finalized.connect(rewrite_links)
