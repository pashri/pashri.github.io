"""Settings for the live build published to GitHub Pages."""

import os
import sys

sys.path.append(os.curdir)

# pylint: disable=wildcard-import,unused-wildcard-import,wrong-import-position
from pelicanconf import *  # noqa: E402,F403

SITEURL = "https://pashri.github.io"
FEED_DOMAIN = SITEURL
RELATIVE_URLS = False
PREVIEW = False
GOATCOUNTER_CODE = "pashri"
