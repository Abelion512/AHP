"""Strip only URL host structure before credential-shape scanning.

Paths, query strings, fragments and userinfo stay in the text that gets
scanned: secrets leak there. Only the scheme and host are structural noise.
The repository's own docs URL prefix is trimmed as known-benign path noise,
without discarding the path text that precedes it.
"""

import re

# Stop at common markdown/HTML delimiters so adjacent URLs stay separate.
_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_BENIGN_PATH_MARKERS = ("AHP",)
_AUTHORITY_END = "/?#"


def _split_authority(rest):
    """Split authority from the tail at the first /, ? or # (any may come first).

    A URL without a slash can still carry a query or fragment; treating those as
    part of the host would drop the credential-shaped value before scanning.
    """
    for index, char in enumerate(rest):
        if char in _AUTHORITY_END:
            return rest[:index], rest[index:]
    return rest, ""


def strip_url_structure(text):
    """Remove scheme and host from URLs; keep userinfo, path, query and fragment."""
    def replace(match):
        rest = match.group(0).split("://", 1)[1]
        authority, tail = _split_authority(rest)
        keep = ""
        if "@" in authority:
            # Keep everything before the final @; an earlier @ may be part of the secret.
            keep += authority.rsplit("@", 1)[0] + "@"
        for marker in _BENIGN_PATH_MARKERS:
            # Drop only the known-benign marker itself. Everything before it stays
            # in the scanned text, so a secret that precedes the marker is caught.
            tail = tail.replace(marker + "/", "")
        return keep + tail

    return _URL.sub(replace, text)
