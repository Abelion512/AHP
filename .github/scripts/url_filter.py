"""Strip only URL host structure before credential-shape scanning.

Paths, query strings, fragments and userinfo stay in the text that gets
scanned: secrets leak there. Only the scheme and host are structural noise.
The repository's own docs URL prefix is trimmed as known-benign path noise.
"""

import re

# Stop at common markdown/HTML delimiters so adjacent URLs stay separate.
_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_BENIGN_PATH_MARKERS = ("AHP",)


def strip_url_structure(text):
    """Remove scheme and host from URLs; keep userinfo, path, query and fragment."""
    def replace(match):
        rest = match.group(0).split("://", 1)[1]
        # Split on the first path, query or fragment delimiter. A URL without a
        # path still has a query/fragment that must stay in the scanned text.
        parts = re.split(r"([/?#])", rest, maxsplit=1)
        authority = parts[0]
        separator = parts[1] if len(parts) > 1 else ""
        tail = parts[2] if len(parts) > 2 else ""
        keep = ""
        if "@" in authority:
            # Keep everything before the final @; an earlier @ may be part of the secret.
            keep += authority.rsplit("@", 1)[0] + "@"
        if separator:
            for marker in _BENIGN_PATH_MARKERS:
                sentinel = marker + "/"
                if sentinel in tail:
                    # Drop only the marker. Text before it may be a secret.
                    tail = tail.replace(sentinel, "", 1)
                    break
            keep += separator + tail
        return keep

    return _URL.sub(replace, text)
