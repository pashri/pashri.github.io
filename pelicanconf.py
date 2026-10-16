"""Settings shared by the preview build and the live build."""

AUTHOR = "Patrick Linton"
SITENAME = "Patrick Linton · Notes"
SITE_DESCRIPTION = "Notes on transport, housing, and climate."
SITE_SUBTITLE = "Short reports on things I've read, seen, or built."
SITESUBTITLE = SITE_DESCRIPTION
SITEURL = ""
PREVIEW = True

PATH = "content"
ARTICLE_PATHS = ["posts"]
PAGE_PATHS = ["pages"]
STATIC_PATHS = ["images"]
THEME = "theme"
DELETE_OUTPUT_DIRECTORY = True
TIMEZONE = "UTC"
DEFAULT_LANG = "en"
DEFAULT_PAGINATION = False
SLUGIFY_SOURCE = "basename"

SUBJECT_TAGS = [
    "Transport",
    "Housing",
    "Placemaking",
    "Climate",
    "Software & data",
]
PLACE_TAGS = ["Sydney", "Cambridge", "New York"]
LINKS = [
    ("LinkedIn", "https://www.linkedin.com/in/plinton/"),
    ("GitHub", "https://github.com/pashri"),
]

ARTICLE_URL = "{ref}/"
ARTICLE_SAVE_AS = "{ref}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
TAG_URL = "tags/{slug}/"
TAG_SAVE_AS = "tags/{slug}/index.html"
TAGS_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
AUTHOR_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
ARCHIVES_SAVE_AS = ""
DIRECT_TEMPLATES = ["index"]
TEMPLATE_PAGES = {"404.html": "404.html"}

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
TAG_FEED_ATOM = None
FEED_ALL_RSS = "feed.xml"
RSS_FEED_SUMMARY_ONLY = False
SUMMARY_MAX_PARAGRAPHS = 1
SUMMARY_MAX_LENGTH = None

MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {
            "css_class": "highlight",
            "guess_lang": False,
        },
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
    },
    "output_format": "html5",
}

PLUGIN_PATHS = ["plugins"]
PLUGINS = [
    "series",
    "sitemap",
    "references",
    "notes_markdown",
    "series_pages",
    "cards",
]
SITEMAP = {"format": "xml", "exclude": ["404.html"]}
GOATCOUNTER_CODE = ""
