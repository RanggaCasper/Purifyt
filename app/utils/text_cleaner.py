import json
import re
import string
import unicodedata
from functools import lru_cache
from pathlib import Path

import emoji

def _is_valid_reverse_mapping_entry(ascii_char: str, glyph: str) -> bool:
    """Validate entries before reversing ascii->glyph into glyph->ascii."""
    if len(ascii_char) != 1 or not ascii_char.isascii() or not glyph:
        return False
    if glyph.isascii():
        return False
    if glyph == ascii_char:
        return False
    return True


def _ascii_target(ascii_char: str) -> str:
    """Normalize ASCII keys to the cleaner output format."""
    return ascii_char.lower() if ascii_char.isalpha() else ascii_char

@lru_cache(maxsize=1)
def _load_unicode_confusable_maps() -> tuple[dict[str, str], dict[str, str]]:
    """Load reverse confusable mappings from data/unicode.json."""
    json_path = Path(__file__).resolve().parents[1].joinpath("data", "unicode.json")
    if json_path is None:
        return {}, {}

    try:
        with json_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}, {}

    single_char_map: dict[str, str] = {}
    sequence_map: dict[str, str] = {}

    if not isinstance(payload, dict):
        return single_char_map, sequence_map

    for style_map in payload.values():
        if not isinstance(style_map, dict):
            continue

        for ascii_char, glyph in style_map.items():
            if not isinstance(ascii_char, str) or not isinstance(glyph, str):
                continue
            if not _is_valid_reverse_mapping_entry(ascii_char, glyph):
                continue

            target = _ascii_target(ascii_char)
            if len(glyph) == 1:
                single_char_map.setdefault(glyph, target)
            else:
                sequence_map.setdefault(glyph, target)

    return single_char_map, sequence_map


_LAYOUT_NORMALIZATION_MAP = {
    # Space variants -> regular space
    "\u3000": " ",
    "\u00a0": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u2002": " ",
    "\u2003": " ",
    "\u2004": " ",
    "\u2005": " ",
    "\u2007": " ",
    "\u2008": " ",
    # Decorative CJK brackets -> remove
    "【": "",
    "】": "",
    "『": "",
    "』": "",
    "「": "",
    "」": "",
    "〖": "",
    "〗": "",
    "〔": "",
    "〕": "",
    "｢": "",
    "｣": "",
    "《": "",
    "》": "",
    "〈": "",
    "〉": "",
}

_JSON_SINGLE_CONFUSABLES, _SEQUENCE_CONFUSABLES = _load_unicode_confusable_maps()
_CONFUSABLES = str.maketrans({
    **_JSON_SINGLE_CONFUSABLES,
    **_LAYOUT_NORMALIZATION_MAP,
})


@lru_cache(maxsize=1)
def _sequence_confusable_pattern() -> re.Pattern[str] | None:
    if not _SEQUENCE_CONFUSABLES:
        return None

    # Longest-first avoids partial replacement for overlapping sequences.
    escaped = sorted((re.escape(token) for token in _SEQUENCE_CONFUSABLES), key=len, reverse=True)
    return re.compile("|".join(escaped))


def _replace_sequence_confusables(text: str) -> str:
    pattern = _sequence_confusable_pattern()
    if pattern is None:
        return text

    return pattern.sub(lambda m: _SEQUENCE_CONFUSABLES[m.group(0)], text)

# Compiled once; matches decorative / non-letter symbol blocks not caught by
# the emoji library, including box-drawing and block-element separators
# (░▒▓ U+2580-259F) used by lingojam-style generators.
_SYMBOL_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\U0001F7E0-\U0001F7FF"  # geometric shapes extended
    "\U00002600-\U000027BF"  # misc symbols & dingbats
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U000024FF"  # enclosed alphanumerics
    "\U00002500-\U000025FF"  # box drawing + block elements + geometric shapes
    "\U00002200-\U000022FF"  # mathematical operators (≋ ∞ etc.)
    "\U00002300-\U000023FF"  # miscellaneous technical
    "]+",
    flags=re.UNICODE,
)

_SUPERSCRIPT_SUBSCRIPT_RE = re.compile(r"[\u00b2\u00b3\u00b9\u2070-\u209f]")
_INVISIBLE_FORMATTING_RE = re.compile(r"[\u200b-\u200f\u200d\u202a-\u202e\u2060\ufeff\u00ad]")
_COMBINING_SYMBOL_MARKS_RE = re.compile(r"[\u20d0-\u20ff]")
_ASCII_SYMBOLS_RE = re.compile("[" + re.escape(string.punctuation) + "]")
_REPEATED_PUNCTUATION_RE = re.compile(r"([.!?,;:~\-]){2,}")
_STANDALONE_REPEATED_CHAR_RE = re.compile(r"\b(\w)\1{3,}\b")
_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s]+"
    r"|"
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}(?:/[^\s]*)?"
)
_URL_TRAILING_PUNCTUATION = ",.!?;:"

_ENCLOSED_LETTER_NAME_PREFIXES = (
    "SQUARED LATIN CAPITAL LETTER ",
    "NEGATIVE SQUARED LATIN CAPITAL LETTER ",
    "CIRCLED LATIN CAPITAL LETTER ",
    "LATIN CAPITAL LETTER ",
    "SQUARED LATIN SMALL LETTER ",
    "NEGATIVE SQUARED LATIN SMALL LETTER ",
    "CIRCLED LATIN SMALL LETTER ",
    "LATIN SMALL LETTER ",
)

# Best-effort transliteration for Unicode names that are not single-letter
# tokens (e.g. CHI -> x). Applied only to non-ASCII alphabetic characters.
_LETTER_NAME_TOKEN_TO_ASCII = {
    "CHI": "x",
    "THETA": "o",
    "LAMBDA": "l",
    "LAMDA": "l",
    "THORN": "p",
    "SCHWA": "e",
}

_LETTER_NAME_IGNORES = {
    "SMALL",
    "CAPITAL",
    "MODIFIER",
    "FINAL",
    "MEDIAL",
    "INITIAL",
    "ISOLATED",
}

_UNICODE_CHAR_FALLBACK_TO_ASCII = {
    # CANADIAN SYLLABICS CARRIER GHEE used as 'r' in fancy-text generators.
    "ᗇ": "r",
}

def _extract_letter_name_tokens(name: str) -> list[str]:
    """Return candidate tokens after 'LETTER' in a Unicode character name."""
    if "LETTER " not in name:
        return []

    tail = name.split("LETTER ", 1)[1]
    tail = tail.split(" WITH ", 1)[0]
    tail = tail.replace("-", " ")

    return [
        token for token in tail.split()
        if token and token not in _LETTER_NAME_IGNORES
    ]


@lru_cache(maxsize=4096)
def _map_unicode_letter_to_ascii(ch: str) -> str:
    """Map non-ASCII alphabetic chars to a best-effort ASCII equivalent."""
    if ch.isascii() or not ch.isalpha():
        return ch

    direct = _UNICODE_CHAR_FALLBACK_TO_ASCII.get(ch)
    if direct:
        return direct

    try:
        name = unicodedata.name(ch)
    except ValueError:
        return ch

    tokens = _extract_letter_name_tokens(name)
    if not tokens:
        return ch

    for token in reversed(tokens):
        if len(token) == 1 and "A" <= token <= "Z":
            return token.lower()

        mapped = _LETTER_NAME_TOKEN_TO_ASCII.get(token)
        if mapped:
            return mapped

    # Final fallback: use the first alphabetic char of the last token
    # (e.g. KA -> k, YA -> y, ALEF -> a).
    for c in tokens[-1]:
        if "A" <= c <= "Z":
            return c.lower()

    return ch


def clean_comment(text: str) -> str:
    """
    Clean the comment text by:
    - Normalizing bold/fancy unicode and collapsing repeated characters
    - Mapping confusable/lookalike characters to ASCII equivalents
    - Removing emojis (using the emoji library and additional unicode ranges)
    - Removing superscripts/subscripts and zero-width/invisible formatting characters
    - Collapsing repeated punctuation and standalone repeated characters
    - Collapsing multiple spaces and stripping
    - Lowercasing the text
    """
    if not text:
        return ""

    text, protected_urls = _protect_urls(text)
    text = _normalize_text(text)
    text = _remove_symbols_and_emoji(text)
    text = _remove_unicode_artifacts(text)
    text = _remove_ascii_symbols(text)
    text = _collapse_repeats_and_spaces(text)
    text = text.lower()
    return _restore_urls(text, protected_urls)


def _protect_urls(text: str) -> tuple[str, dict[str, str]]:
    """Replace URL-like tokens with placeholders so they survive cleaning."""
    protected_urls: dict[str, str] = {}

    def _replace(match: re.Match[str]) -> str:
        token = match.group(0)
        trailing = ""
        while token and token[-1] in _URL_TRAILING_PUNCTUATION:
            trailing = token[-1] + trailing
            token = token[:-1]

        if not token:
            return trailing

        key = f"urltoken{len(protected_urls)}placeholder"
        protected_urls[key] = token
        return f"{key}{trailing}"

    return _URL_RE.sub(_replace, text), protected_urls


def _restore_urls(text: str, protected_urls: dict[str, str]) -> str:
    """Restore original URL tokens after normalization and symbol cleanup."""
    for placeholder, original_url in protected_urls.items():
        text = text.replace(placeholder, original_url)
    return text


def _remove_symbols_and_emoji(text: str) -> str:
    """Remove emoji and decorative symbol blocks."""
    text = emoji.replace_emoji(text, replace="")
    return _SYMBOL_RE.sub("", text)


def _remove_unicode_artifacts(text: str) -> str:
    """Remove formatting/invisible marks often present in decorated text."""
    text = _SUPERSCRIPT_SUBSCRIPT_RE.sub("", text)
    text = _INVISIBLE_FORMATTING_RE.sub("", text)
    # Includes U+20E3 keycap and U+20DE enclosing square marks.
    return _COMBINING_SYMBOL_MARKS_RE.sub("", text)


def _remove_ascii_symbols(text: str) -> str:
    """Remove ASCII punctuation symbols like , . ! ? / from regular text."""
    return _ASCII_SYMBOLS_RE.sub(" ", text)


def _collapse_repeats_and_spaces(text: str) -> str:
    """Normalize repeated punctuation/chars and collapse whitespace."""
    text = _REPEATED_PUNCTUATION_RE.sub(r"\1", text)
    text = _STANDALONE_REPEATED_CHAR_RE.sub(r"\1", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _demojize_enclosed_letters(ch: str) -> str:
    """Convert enclosed/squared/circled latin letters to plain letters."""
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return ch

    for prefix in _ENCLOSED_LETTER_NAME_PREFIXES:
        if name.startswith(prefix):
            letter = name[len(prefix):]
            if len(letter) == 1 and "A" <= letter <= "Z":
                return letter if "CAPITAL" in name else letter.lower()

    return ch


def _normalize_text(text: str, max_repeat: int = 2) -> str:
    # NFKC: handles math-alphabet variants, fullwidth chars, superscript letters
    text = unicodedata.normalize("NFKC", text)

    # Replace multi-character confusable sequences from unicode.json.
    text = _replace_sequence_confusables(text)

    # Map confusable/lookalike chars (small caps, Cyrillic, Greek, IPA, etc.)
    text = text.translate(_CONFUSABLES)

    # Fallback for enclosed letters not handled by NFKC (e.g. 🆁 🅰)
    text = "".join(_demojize_enclosed_letters(ch) for ch in text)

    # Generic fallback for non-ASCII letters across many alphabets.
    text = "".join(_map_unicode_letter_to_ascii(ch) for ch in text)

    # NFKD + strip combining marks: handles diacritics and Zalgo text
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    text = re.sub(r"(.)\1{" + str(max_repeat) + r",}", r"\1" * max_repeat, text)

    return text
