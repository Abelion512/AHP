"""Case changes must never flip a field's classification."""
import importlib
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
cred = importlib.import_module("nebula._credentials")


def _spellings(word: str, rng: random.Random) -> list[str]:
    return [word.lower(), word.upper(), word.title(),
            "".join(rng.choice((ch.lower(), ch.upper())) for ch in word)]


def test_casefold_never_flips_vocabulary_words():
    rng = random.Random(20261120)
    for word in cred._FIELD_WORD_ORDER:
        expected = cred.classify_field(word.lower())
        for variant in _spellings(word, rng):
            assert cred.classify_field(variant) == expected, variant


def test_casefold_never_flips_delimited_and_compound_names():
    rng = random.Random(20261121)
    bases = ["api-key", "service_password", "account.sid", "clientId",
             "api_key_name", "publicKey", "tokenCount"]
    for base in bases:
        expected = cred.classify_field(base)
        for variant in _spellings(base, rng):
            assert cred.classify_field(variant) == expected, variant


def test_casefold_is_stable_under_repeated_mixed_case():
    rng = random.Random(20261122)
    for base in ("password", "secretKeyValue", "compass", "maxTokens"):
        expected = cred.classify_field(base)
        for _ in range(50):
            variant = "".join(rng.choice((ch.lower(), ch.upper())) for ch in base)
            assert cred.classify_field(variant) == expected, variant
