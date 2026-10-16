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
from PIL import Image

EMBED_LINE: Final[re.Pattern[str]] = re.compile(
    pattern=r"\{%\s*embed\s+(?P<attrs>.*?)\s*%\}",
)
EMBED_ATTR: Final[re.Pattern[str]] = re.compile(pattern=r'(\w+)="([^"]*)"')
RELATIVE_LINK: Final[re.Pattern[str]] = re.compile(
    pattern=r'\b(src|href|data-src|data-data)="(?![a-z]+:|/|#)([^"]+)"',
)
POST_URL_TOKEN: Final[str] = "__POST_URL__"
IMG_TAG: Final[re.Pattern[str]] = re.compile(pattern=r"<img\b[^>]*>")
RELATIVE_SRC: Final[re.Pattern[str]] = re.compile(
    pattern=r'\bsrc="(?![a-z]+:|/|#)([^"]+)"',
)
SVG_VIEWBOX: Final[re.Pattern[str]] = re.compile(
    pattern=r'viewBox="[\d.-]+[\s,]+[\d.-]+[\s,]+([\d.]+)[\s,]+([\d.]+)"',
)


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
    figcaption = (
        f"<figcaption>{html.escape(caption)}</figcaption>"
        if caption
        else ""
    )
    return (
        f'<figure class="embed" data-src="{html.escape(attrs["src"])}"'
        f' data-data="{html.escape(attrs["data"])}">'
        '<div class="embed-mount"></div>'
        f'<p class="embed-fallback"><a href="{POST_URL_TOKEN}">'
        "Interactive figure: view it on the site</a></p>"
        f"{figcaption}</figure>"
    )


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
        match = EMBED_LINE.fullmatch(string=line.strip())
        if match is None:
            return line
        attrs = dict(EMBED_ATTR.findall(string=match["attrs"]))
        return self.md.htmlStash.store(html=embed_html(attrs=attrs))


class FigureTreeprocessor(Treeprocessor):
    """Turn a paragraph holding only an image into a figure."""

    # pylint: disable=too-few-public-methods

    def run(self, root: etree.Element) -> None:
        """Convert every lone-image paragraph under ``root``.

        Parameters
        ----------
        root : etree.Element
            The parsed document.
        """
        for para in list(root.iter(tag="p")):
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
    return (
        len(para) == 1
        and para[0].tag == "img"
        and not (para.text or "").strip()
        and not (para[0].tail or "").strip()
    )


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
        md.preprocessors.register(
            item=EmbedPreprocessor(md=md),
            name="notes_embed",
            priority=25,
        )
        md.treeprocessors.register(
            item=FigureTreeprocessor(md=md),
            name="notes_figure",
            priority=15,
        )


def add_extension(pelican: Pelican) -> None:
    """Add the extension to Pelican's Markdown settings.

    Parameters
    ----------
    pelican : Pelican
        The Pelican instance being initialised.
    """
    pelican.settings["MARKDOWN"].setdefault("extensions", []).append(
        NotesExtension(),
    )


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
        shutil.copytree(
            src=folder,
            dst=output / Path(post.save_as).parent,
            dirs_exist_ok=True,
        )


def image_size(path: Path) -> tuple[int, int] | None:
    """Read an image's intrinsic width and height.

    Parameters
    ----------
    path : Path
        A raster image, or an SVG with a ``viewBox``.

    Returns
    -------
    tuple[int, int] | None
        Width and height in pixels, or None if the file is missing or an
        SVG has no ``viewBox``.
    """
    if not path.is_file():
        return None
    if path.suffix.lower() == ".svg":
        match = SVG_VIEWBOX.search(string=path.read_text(encoding="utf-8"))
        return (
            (round(float(match[1])), round(float(match[2])))
            if match
            else None
        )
    with Image.open(fp=path) as image:
        return image.size


def size_image(tag: str, folder: Path) -> str:
    """Add ``loading``, ``width`` and ``height`` to one ``<img>`` tag.

    Attributes the tag already has are left alone.

    Parameters
    ----------
    tag : str
        One ``<img ...>`` tag, with its ``src`` still relative.
    folder : Path
        The Post's attachment folder the ``src`` is relative to.

    Returns
    -------
    str
        The tag with the missing attributes added.
    """
    src = RELATIVE_SRC.search(string=tag)
    size = image_size(path=folder / src[1]) if src else None
    extra = [] if "loading=" in tag else ['loading="lazy"']
    if size and "width=" not in tag:
        extra += [f'width="{size[0]}"', f'height="{size[1]}"']
    return tag[:4] + "".join(f" {attribute}" for attribute in extra) + tag[4:]


def rewrite_post(post: Article, site_url: str) -> None:
    """Size a Post's images and point its relative links at its address.

    Parameters
    ----------
    post : Article
        The Post to rewrite.
    site_url : str
        The site's base URL; empty in the preview build.
    """
    base = f"{site_url}/{post.url}"
    folder = Path(post.source_path).with_suffix("")
    content = IMG_TAG.sub(
        repl=lambda match: size_image(tag=match[0], folder=folder),
        string=post._content,  # pylint: disable=protected-access
    )
    content = RELATIVE_LINK.sub(
        repl=lambda match: f'{match[1]}="{base}{match[2]}"',
        string=content,
    )
    post._content = content.replace(  # pylint: disable=protected-access
        POST_URL_TOKEN,
        f"{site_url}/{post.url}",
    )


def register() -> None:
    """Connect the plugin to Pelican's signals."""
    signals.initialized.connect(receiver=add_extension)
    signals.article_generator_finalized.connect(receiver=rewrite_links)
