"""Strip only URL host structure before credential-shape scanning.

Paths, query strings, fragments and userinfo stay in the text that gets
scanned: secrets leak there. Only the scheme and host are structural noise.
The repository's own docs URL prefix is trimmed as known-benign path noise.
"""

import re

# Stop at common markdown/HTML delimiters so adjacent URLs stay separate.
_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_BENIGN_PATH_PREFIXES = ("Abelion512/AHP/",)


def strip_url_structure(text):
    """Remove scheme and host from URLs; keep userinfo, path, query and fragment."""
    def replace(match):
        rest = match.group(0).split("://", 1)[1]
        authority, separator, tail = rest.partition("/")
        keep = ""
        if "@" in authority:
            # Keep everything before the final @; an earlier @ may be part of the secret.
            keep += authority.rsplit("@", 1)[0] + "@"
        if separator:
            for prefix in _BENIGN_PATH_PREFIXES:
                if tail.startswith(prefix):
                    tail = tail[len(prefix):]
                    break
            keep += "/" + tail
        return keep

    return _URL.sub(replace, text)
