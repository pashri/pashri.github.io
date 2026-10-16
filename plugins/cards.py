"""Draw a link-preview card image for each Post with a headless browser."""

import hashlib
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import unquote

from jinja2 import Environment, FileSystemLoader, Template
from pelican import Pelican, signals
from pelican.contents import Article
from pelican.generators import ArticlesGenerator
from playwright.sync_api import ViewportSize, sync_playwright

logger = logging.getLogger(__name__)

CARD_SIZE: Final[ViewportSize] = {"width": 1200, "height": 630}
CACHE_DIR: Final[Path] = Path(".cache/cards")
POSTS: Final[list[Article]] = []
FIT_TITLE: Final[str] = """() => {
  const title = document.querySelector(".title");
  let size = parseFloat(getComputedStyle(title).fontSize);
  while (title.scrollHeight > title.clientHeight && size > 28) {
    size -= 2;
    title.style.fontSize = `${size}px`;
  }
}"""


@dataclass(frozen=True)
class Card:
    """One card to draw.

    Attributes
    ----------
    html : str
        The rendered card page.
    target : Path
        Where the PNG goes in the output.
    """

    html: str
    target: Path


def title_size(title: str, has_image: bool) -> int:
    """Pick a font size so the title fits the card.

    Parameters
    ----------
    title : str
        The Post title.
    has_image : bool
        True when the title shares the card with an image.

    Returns
    -------
    int
        Font size in pixels.
    """
    sizes = (64, 52, 42) if has_image else (88, 72, 58)
    limits = (40, 75) if has_image else (45, 85)
    return next(
        (
            size
            for size, limit in zip(sizes, limits)
            if len(title) <= limit
        ),
        sizes[-1],
    )


def remember(generator: ArticlesGenerator) -> None:
    """Keep the published Posts for drawing once the build finishes.

    Parameters
    ----------
    generator : ArticlesGenerator
        Pelican's article generator.
    """
    POSTS.clear()
    POSTS.extend(
        post
        for post in generator.articles
        if "ref" in post.metadata
    )


def image_uri(post: Article) -> str:
    """Return a file URI for the Post's card image, or an empty string.

    Parameters
    ----------
    post : Article
        A Post that may set ``Image:``.

    Returns
    -------
    str
        A ``file://`` URI, or ``""`` when the Post has no image.
    """
    name = post.metadata.get("image")
    if not name:
        return ""
    folder = Path(post.source_path).with_suffix("")
    return (folder / name).resolve().as_uri()


def post_card(post: Article, template: Template, settings: dict) -> str:
    """Render the card HTML for one Post.

    Parameters
    ----------
    post : Article
        A published Post.
    template : Template
        The ``card.html`` template.
    settings : dict
        Pelican settings holding SITENAME and THEME.

    Returns
    -------
    str
        The card page as HTML.
    """
    image = image_uri(post=post)
    kicker = (
        f"Notes · {post.ref}"
        if image
        else f"{settings['SITENAME']} · {post.ref}"
    )
    fonts = Path(settings["THEME"]).resolve() / "static" / "fonts"
    return template.render(
        fonts=fonts.as_uri(),
        image=image,
        kicker=kicker,
        title=post.title,
        tags=" · ".join(tag.name for tag in post.ordered_tags),
        title_size=title_size(title=post.title, has_image=bool(image)),
    )


def build_cards(pelican: Pelican) -> list[Card]:
    """Render the HTML for the site card and every Post's card.

    Parameters
    ----------
    pelican : Pelican
        The finished Pelican run.

    Returns
    -------
    list[Card]
        One card per published Post, plus the site card.
    """
    settings, output = pelican.settings, Path(pelican.output_path)
    theme = Path(settings["THEME"]).resolve()
    template = Environment(
        loader=FileSystemLoader(searchpath=theme / "templates"),
        autoescape=True,
    ).get_template(name="card.html")
    site_card = Card(
        html=template.render(
            fonts=(theme / "static" / "fonts").as_uri(),
            image="",
            kicker=settings["SITENAME"],
            title=settings["SITE_DESCRIPTION"],
            title_size=72,
            tags=settings["SITE_SUBTITLE"],
        ),
        target=output / "card.png",
    )
    return [site_card] + [
        Card(
            html=post_card(post=post, template=template, settings=settings),
            target=output / post.ref / "card.png",
        )
        for post in POSTS
    ]


def cache_path(card: Card) -> Path:
    """Return where a card's PNG is cached, keyed by its HTML and image.

    Parameters
    ----------
    card : Card
        The card to look up.

    Returns
    -------
    Path
        A path under ``.cache/cards/``.
    """
    digest = hashlib.sha256(card.html.encode(encoding="utf-8"))
    uris = [
        part
        for part in card.html.split('"')
        if part.startswith("file://")
        and not part.endswith("fonts")
    ]
    for uri in uris:
        path = Path(unquote(string=uri.removeprefix("file://")))
        if path.is_file():
            digest.update(path.read_bytes())
    return CACHE_DIR / f"{digest.hexdigest()}.png"


def draw(cards: list[Card]) -> None:
    """Screenshot every card that isn't cached yet.

    Parameters
    ----------
    cards : list[Card]
        The cards to draw.
    """
    pending = [card for card in cards if not cache_path(card=card).exists()]
    if pending:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport=CARD_SIZE)
            for card in pending:
                source = cache_path(card=card).with_suffix(".html")
                source.write_text(data=card.html, encoding="utf-8")
                page.goto(url=source.resolve().as_uri(), wait_until="load")
                page.evaluate(expression=FIT_TITLE)
                page.screenshot(path=cache_path(card=card))
            browser.close()
    logger.info(
        "cards: drew %d, reused %d",
        len(pending),
        len(cards) - len(pending),
    )


def publish_cards(pelican: Pelican) -> None:
    """Draw any new cards and copy every card into the output.

    Parameters
    ----------
    pelican : Pelican
        The finished Pelican run.
    """
    cards = build_cards(pelican=pelican)
    draw(cards=cards)
    for card in cards:
        card.target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src=cache_path(card=card), dst=card.target)


def register() -> None:
    """Connect the plugin to Pelican's signals."""
    signals.article_generator_finalized.connect(receiver=remember)
    signals.finalized.connect(receiver=publish_cards)
