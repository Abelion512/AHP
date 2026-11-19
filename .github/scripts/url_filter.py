"""Strip only the structural part of a URL before credential-shape scanning.

Query strings, fragments and userinfo are kept on purpose: secrets leak there,
and removing the whole URL would hide those shapes from the credential guard.
"""

import re

_URL = re.compile(r"https?://\S+")


def strip_url_structure(text):
    """Remove scheme, host and path from URLs; keep userinfo, query and fragment."""
    def replace(match):
        rest = match.group(0).split("://", 1)[1]
        authority = rest.split("/", 1)[0]
        keep = ""
        if "@" in authority:
            keep += authority.split("@", 1)[0] + "@"
        for marker in ("?", "#"):
            index = rest.find(marker)
            if index != -1:
                keep += rest[index:]
                break
        return keep

    return _URL.sub(replace, text)
