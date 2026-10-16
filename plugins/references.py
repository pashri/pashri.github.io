"""Check References and Tags, and route Posts that have no Reference."""

import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Final

from pelican import signals
from pelican.contents import Article
from pelican.generators import ArticlesGenerator

logger = logging.getLogger(__name__)

REF_PATTERN: Final[re.Pattern[str]] = re.compile(pattern=r"(\d{2})/(\d{3})")
FIRST_PARA: Final[re.Pattern[str]] = re.compile(
    pattern=r"^<p>(.*?)</p>",
    flags=re.MULTILINE | re.DOTALL,
)
FN_REF: Final[re.Pattern[str]] = re.compile(
    pattern=r'<sup id="fnref[^"]*">.*?</sup>',
)


class ContentCheckError(Exception):
    """Raised when Posts break the Reference or Tag rules."""


def route_unpublished(instance: object) -> None:
    """Route a Post without a Reference to /unpublished/; skip hidden Posts.

    A hidden Post keeps its Reference but no page is written for it.

    Parameters
    ----------
    instance : object
        Any content object Pelican has just created.
    """
    if not isinstance(instance, Article):
        return
    if instance.status == "hidden":
        instance.override_save_as = ""
    if "ref" in instance.metadata:
        return
    stem = Path(instance.source_path).stem
    instance.override_url = f"unpublished/{stem}/"
    instance.override_save_as = f"unpublished/{stem}/index.html"


def describe(article: Article) -> str:
    """Return the text used for a Post's meta description.

    Parameters
    ----------
    article : Article
        The Post to describe.

    Returns
    -------
    str
        The ``Summary:`` field if set, else the first top-level prose
        paragraph with footnote numbers removed. May contain HTML tags.
    """
    if "summary" in article.metadata:
        return str(article.metadata["summary"])
    match = FIRST_PARA.search(
        string=article._content,  # pylint: disable=protected-access
    )
    return FN_REF.sub(repl="", string=match[1]) if match else ""


def annotate(article: Article, tag_order: list[str]) -> None:
    """Attach the attributes the templates read.

    Parameters
    ----------
    article : Article
        The Post to annotate.
    tag_order : list[str]
        Subject Tags then place Tags, in display order.
    """
    match = REF_PATTERN.fullmatch(string=article.metadata.get("ref", ""))
    article.unpublished = "ref" not in article.metadata
    article.description = describe(article=article)
    article.ref_year = f"20{match[1]}" if match else ""
    article.ordered_tags = sorted(
        getattr(article, "tags", []),
        key=lambda tag: (
            tag_order.index(tag.name)
            if tag.name in tag_order
            else len(tag_order)
        ),
    )


def tag_problems(article: Article, settings: dict) -> list[str]:
    """List the Tag rules a Post breaks.

    Parameters
    ----------
    article : Article
        The Post to check.
    settings : dict
        Pelican settings holding SUBJECT_TAGS and PLACE_TAGS.

    Returns
    -------
    list[str]
        One message per problem, prefixed with the file name.
    """
    name = Path(article.source_path).name
    tags = [tag.name for tag in getattr(article, "tags", [])]
    allowed = settings["SUBJECT_TAGS"] + settings["PLACE_TAGS"]
    problems = [
        f"{name}: unknown tag '{tag}'"
        for tag in tags
        if tag not in allowed
    ]
    if not set(tags) & set(settings["SUBJECT_TAGS"]):
        problems.append(f"{name}: no subject tag")
    return problems


def image_problems(article: Article) -> list[str]:
    """Report an ``Image:`` field that names a file that doesn't exist.

    Parameters
    ----------
    article : Article
        The Post to check.

    Returns
    -------
    list[str]
        One message if the image is missing, otherwise none.
    """
    name = article.metadata.get("image")
    folder = Path(article.source_path).with_suffix("")
    if not name or (folder / name).is_file():
        return []
    return [
        f"{Path(article.source_path).name}: Image '{name}' not found "
        f"in {folder.name}/",
    ]


def ref_problems(article: Article, preview: bool) -> list[str]:
    """List the Reference rules one Post breaks on its own.

    Parameters
    ----------
    article : Article
        The Post to check.
    preview : bool
        True in the preview build, where a missing Reference is allowed.

    Returns
    -------
    list[str]
        One message per problem, prefixed with the file name.
    """
    name = Path(article.source_path).name
    ref = article.metadata.get("ref")
    if ref is None:
        return [] if preview else [f"{name}: missing Ref"]
    match = REF_PATTERN.fullmatch(string=ref)
    if match is None:
        return [f"{name}: malformed Ref '{ref}'"]
    if match[1] != f"{article.date.year % 100:02d}":
        return [
            f"{name}: Ref {ref} doesn't match Date "
            f"{article.date:%Y-%m-%d}",
        ]
    return []


def sequence_problems(articles: list[Article]) -> list[str]:
    """Find duplicate References and gaps in each year's numbering.

    Parameters
    ----------
    articles : list[Article]
        Every Post, published or hidden.

    Returns
    -------
    list[str]
        One message per duplicate and per missing number.
    """
    users: dict[str, list[str]] = defaultdict(list)
    for article in articles:
        if REF_PATTERN.fullmatch(string=article.metadata.get("ref", "")):
            users[article.metadata["ref"]].append(
                Path(article.source_path).name,
            )
    problems = [
        f"Ref {ref} is used by {' and '.join(sorted(names))}"
        for ref, names in sorted(users.items())
        if len(names) > 1
    ]
    numbers: dict[str, set[int]] = defaultdict(set)
    for ref in users:
        numbers[ref[:2]].add(int(ref[3:]))
    problems += [
        f"gap in 20{year}: {year}/{missing:03d} is missing"
        for year, taken in sorted(numbers.items())
        for missing in sorted(set(range(1, max(taken) + 1)) - taken)
    ]
    return problems


def check(generator: ArticlesGenerator) -> None:
    """Annotate every Post, then fail the build if any rule is broken.

    Parameters
    ----------
    generator : ArticlesGenerator
        Pelican's article generator, after it has read every Post.

    Raises
    ------
    ContentCheckError
        In the live build, after logging every problem as a warning.
    """
    settings = generator.settings
    posts = generator.articles + generator.hidden_articles
    for post in posts:
        annotate(
            article=post,
            tag_order=settings["SUBJECT_TAGS"] + settings["PLACE_TAGS"],
        )
    problems = [
        problem
        for post in posts
        for problem in (
            ref_problems(article=post, preview=settings["PREVIEW"])
            + tag_problems(article=post, settings=settings)
            + image_problems(article=post)
        )
    ]
    problems += sequence_problems(articles=posts)
    for problem in problems:
        logger.warning(problem)
    if problems and not settings["PREVIEW"]:
        raise ContentCheckError(
            f"{len(problems)} content problem(s); see the warnings above",
        )


def register() -> None:
    """Connect the plugin to Pelican's signals."""
    signals.content_object_init.connect(receiver=route_unpublished)
    signals.article_generator_finalized.connect(receiver=check)
