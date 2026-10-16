"""Commands for previewing the site and publishing a Post."""

import re
import sys
from datetime import date
from pathlib import Path
from typing import Final

import pelican

SITE_URL: Final[str] = "https://pashri.github.io"
REF_LINE: Final[re.Pattern[str]] = re.compile(
    pattern=r"^ref:\s*(\d{2})/(\d{3})\s*$",
    flags=re.IGNORECASE,
)
STAMPED_LINE: Final[re.Pattern[str]] = re.compile(
    pattern=r"^(ref|date):",
    flags=re.IGNORECASE,
)


def preview() -> None:
    """Serve the site on localhost:8000 and rebuild on every save."""
    pelican.main(
        argv=[
            "content",
            "-s",
            "pelicanconf.py",
            "-o",
            "output",
            "--listen",
            "--autoreload",
            "--port",
            "8000",
            *sys.argv[1:],
        ],
    )


def header_lines(text: str) -> tuple[list[str], str]:
    """Split a Post into its header lines and its body.

    Parameters
    ----------
    text : str
        The whole Markdown file.

    Returns
    -------
    tuple[list[str], str]
        The header lines, and everything after the first blank line.
    """
    header, _, body = text.partition("\n\n")
    return header.splitlines(), body


def next_ref(today: date, posts_dir: Path) -> str:
    """Return the next free Reference for today's year.

    Parameters
    ----------
    today : date
        The publishing date; its year picks the sequence.
    posts_dir : Path
        The folder holding every Post.

    Returns
    -------
    str
        A Reference such as ``26/015``.
    """
    year = f"{today.year % 100:02d}"
    taken = [
        int(match[2])
        for path in posts_dir.glob(pattern="*.md")
        for line in header_lines(
            text=path.read_text(encoding="utf-8"),
        )[0]
        if (match := REF_LINE.match(string=line)) and match[1] == year
    ]
    return f"{year}/{max(taken, default=0) + 1:03d}"


def stamp(lines: list[str], ref: str, today: date) -> list[str]:
    """Return header lines with a fresh Date and the new Ref.

    Parameters
    ----------
    lines : list[str]
        The Post's header lines.
    ref : str
        The Reference to add.
    today : date
        The date to write.

    Returns
    -------
    list[str]
        The header with Date and Ref placed after the Title line.
    """
    kept = [
        line
        for line in lines
        if not STAMPED_LINE.match(string=line)
    ]
    title_at = next(
        (
            index
            for index, line in enumerate(kept)
            if line.lower().startswith("title:")
        ),
        -1,
    )
    return (
        kept[:title_at + 1]
        + [f"Date: {today:%Y-%m-%d}", f"Ref: {ref}"]
        + kept[title_at + 1:]
    )


def publish() -> None:
    """Give a Post the next free Reference and today's date."""
    if len(sys.argv) != 2:
        sys.exit("usage: uv run publish content/posts/<file>.md")
    path = Path(sys.argv[1])
    lines, body = header_lines(text=path.read_text(encoding="utf-8"))
    if any(line.lower().startswith("ref:") for line in lines):
        sys.exit(f"{path.name} already has a Ref")
    today = date.today()
    ref = next_ref(today=today, posts_dir=path.parent)
    header = "\n".join(stamp(lines=lines, ref=ref, today=today))
    path.write_text(data=f"{header}\n\n{body}", encoding="utf-8")
    print(
        f"{path.name}: Ref {ref}. Live at {SITE_URL}/{ref}/ "
        "once you commit and push.",
    )
