import re
import unicodedata
from functools import lru_cache

import emoji

# Characters commonly substituted for Latin letters in fancy text generators
# (e.g. lingojam.com). Applied after NFKC so math-alphabet variants are
# already normalised before we reach this table.
_CONFUSABLES = str.maketrans({
    # Small capital letters
    'ʀ': 'r', 'ᴀ': 'a', 'ɴ': 'n', 'ɢ': 'g', 'ᴄ': 'c', 'ꜱ': 's', 'ᴘ': 'p',
    'ᴇ': 'e', 'ʙ': 'b', 'ᴅ': 'd', 'ꜰ': 'f', 'ʜ': 'h', 'ɪ': 'i', 'ᴊ': 'j',
    'ᴋ': 'k', 'ʟ': 'l', 'ᴍ': 'm', 'ᴏ': 'o', 'ᴛ': 't', 'ᴜ': 'u', 'ᴠ': 'v',
    'ᴡ': 'w', 'ʏ': 'y', 'ᴢ': 'z',
    # IPA / extended Latin used as aesthetic substitutes
    'ɛ': 'e', 'ƈ': 'c', 'ɠ': 'g', 'ɦ': 'h', 'ŋ': 'n', 'ɳ': 'n', 'ɱ': 'm',
    'ɾ': 'r', 'ɹ': 'r', 'ʁ': 'r', 'ʂ': 's', 'ƒ': 'f', 'ʋ': 'v', 'ʐ': 'z',
    'ɓ': 'b', 'ɗ': 'd', 'ƥ': 'p', 'ƭ': 't', 'ƙ': 'k',
    # Upside-down / mirrored
    'ǝ': 'e', 'ɔ': 'c', 'ʌ': 'v', 'ɯ': 'w', 'ʇ': 't', 'ʎ': 'y', 'ᴉ': 'i',
    # Cyrillic lookalikes
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',
    'м': 'm', 'н': 'h', 'т': 't', 'к': 'k', 'в': 'b', 'я': 'r', 'г': 'r',
    'є': 'e', 'ѕ': 's',
    # Greek lookalikes
    'α': 'a', 'η': 'n', 'ν': 'v', 'ρ': 'p', 'τ': 't', 'υ': 'u', 'ω': 'w',
    'χ': 'x', 'ι': 'i', 'σ': 'o', 'ς': 'c',
    # Armenian lookalikes
    'ռ': 'n', 'զ': 'q', 'փ': 'p', 'ք': 'p', 'ֆ': 's',
    'օ': 'o', 'ղ': 'n', 'է': 't', 'ҍ': 'b', 'Ӏ': 'l', 'ӄ': 'k',
    '\u049f': 'k',  # ҟ CYRILLIC SMALL LETTER KA WITH STROKE
    # Extended IPA / Latin extensions
    'ƚ': 'l', 'ʅ': 'l', 'ɮ': 'b', 'ȶ': 't', 'ɫ': 'l',
    # Greek capital lookalikes
    'Λ': 'a', 'Θ': 'o', 'θ': 'o', 'Σ': 's', 'Ω': 'o', 'Π': 'n',
    # Cyrillic capital lookalikes
    'Я': 'r', 'А': 'a', 'Е': 'e', 'О': 'o', 'Р': 'r', 'С': 'c',
    'У': 'y', 'Х': 'x', 'М': 'm', 'К': 'k', 'В': 'b', 'Т': 't',
    'П': 'n', 'Н': 'h',
    # O with stroke (used as 'o' substitute)
    'Ø': 'o', 'ø': 'o',
    # Cyrillic barred O
    '\u04e8': 'o', '\u04e9': 'o',  # Ө ө
    # Latin T/L with hooks (uppercase variants not decomposed by NFKD)
    '\u01ac': 't', '\u01ad': 't',  # Ƭ ƭ (capital, lowercase already in table)
    # Hangul jamo used as letter substitute
    '\u3134': 'l',  # ᄂ HANGUL COMPATIBILITY JAMO NIEUN (looks like L)
    '\u1102': 'l',  # ᄂ HANGUL LETTER NIEUN (precomposed)
    # Currency symbols used as letters in lingojam
    '₭': 'k', '₳': 'a', '₦': 'n', '₮': 't', '₵': 'c', '฿': 'b',
    'Ɽ': 'r', 'Ⱡ': 'l',
    # Canadian Aboriginal Syllabics (common lingojam substitutes, hex escapes for safety)
    '\u15e9': 'a',  # ᗩ
    '\u144e': 'n',  # ᑎ
    '\u15c7': 'r',  # ᖇ
    '\u15f7': 'b',  # ᗷ
    '\u14aa': 'l',  # ᒪ
    '\u1455': 'c',  # ᑕ
    '\u1515': 's',  # ᔕ
    '\u146d': 'p',  # ᑭ
    '\u15b6': 't',  # ᖶ
    '\u14aa': 'l',  # ᒪ (duplicate-safe)
    '\u1538': 'o',  # ᔸ (similar to o)
    '\u1550': 't',  # ᕐ-like
    # Script / symbol substitutes
    '℘': 'p',
    # Space variants → regular space
    '\u3000': ' ', '\u00a0': ' ', '\u2009': ' ', '\u200a': ' ',
    '\u2002': ' ', '\u2003': ' ', '\u2004': ' ', '\u2005': ' ',
    '\u2007': ' ', '\u2008': ' ',
    # Decorative CJK brackets → remove
    '【': '', '】': '', '『': '', '』': '', '「': '', '」': '',
    '〖': '', '〗': '', '〔': '', '〕': '', '｢': '', '｣': '',
    '《': '', '》': '', '〈': '', '〉': '',
})

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

# Best-effort transliteration for Unicode names that are not single-letter
# tokens (e.g. CHI -> x). Applied only to non-ASCII alphabetic characters.
_LETTER_NAME_TOKEN_TO_ASCII = {
    "CHI": "x",
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

    text = _normalize_text(text)

    text = emoji.replace_emoji(text, replace="")

    text = _SYMBOL_RE.sub("", text)

    # Remove superscripts and subscripts (², ³, ¹, ⁰-⁹, ₀-₉, etc.)
    text = re.sub(r"[\u00b2\u00b3\u00b9\u2070-\u209f]", "", text)

    # Remove zero-width and invisible formatting characters
    text = re.sub(r"[\u200b-\u200f\u200d\u202a-\u202e\u2060\ufeff\u00ad]", "", text)

    # Remove combining diacritical marks for symbols (U+20D0-U+20FF) including
    # U+20E3 COMBINING ENCLOSING KEYCAP and U+20DE COMBINING ENCLOSING SQUARE
    # which have combining class 0 and are missed by the NFKD filter above.
    text = re.sub(r"[\u20d0-\u20ff]", "", text)

    # Collapse repeated punctuation (.. → ., ,,, → ,, !!! → !, etc.)
    text = re.sub(r'([.!?,;:~\-]){2,}', r'\1', text)

    # Remove standalone repeated characters (e.g "aaaa", "wwwww")
    text = re.sub(r'\b(\w)\1{3,}\b', r'\1', text)

    text = re.sub(r"\s+", " ", text).strip()

    text = text.lower()

    return text


def _demojize_enclosed_letters(ch: str) -> str:
    """Convert enclosed/squared/circled latin letters to plain letters."""
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return ch

    patterns = [
        "SQUARED LATIN CAPITAL LETTER ",
        "NEGATIVE SQUARED LATIN CAPITAL LETTER ",
        "CIRCLED LATIN CAPITAL LETTER ",
        "LATIN CAPITAL LETTER ",
        "SQUARED LATIN SMALL LETTER ",
        "NEGATIVE SQUARED LATIN SMALL LETTER ",
        "CIRCLED LATIN SMALL LETTER ",
        "LATIN SMALL LETTER ",
    ]

    for p in patterns:
        if name.startswith(p):
            letter = name[len(p):]
            if len(letter) == 1 and "A" <= letter <= "Z":
                return letter if "CAPITAL" in name else letter.lower()

    return ch


def _normalize_text(text: str, max_repeat: int = 2) -> str:
    # NFKC: handles math-alphabet variants, fullwidth chars, superscript letters
    text = unicodedata.normalize("NFKC", text)

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
