import re
import unicodedata

import emoji

def clean_comment(text: str) -> str:
    """
    Clean the comment text by:
    - Normalizing bold/fancy unicode and collapsing repeated characters
    - Removing emojis (using the emoji library and additional unicode ranges)
    - Removing superscripts/subscripts and zero-width/invisible formatting characters
    - Collapsing repeated punctuation and standalone repeated characters
    - Collapsing multiple spaces and stripping
    - Lowercasing the text
    """
    if not text:
        return ""
    
    # Normalize bold/fancy unicode and collapse repeated characters
    text = _normalize_text(text)

    # Remove all emojis detected by the emoji library
    text = emoji.replace_emoji(text, replace="")

    # Remove remaining emoji/symbol unicode ranges not caught by the library
    text = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U0001F7E0-\U0001F7FF"  # geometric shapes extended (🟣, 🟢, etc.)
        "\U00002600-\U000027BF"  # misc symbols & dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U000024FF"  # enclosed alphanumerics
        "]+",
        flags=re.UNICODE,
    ).sub(" ", text)

    # Remove superscripts and subscripts (², ³, ¹, ⁰-⁹, ₀-₉, etc.)
    text = re.sub(r"[\u00b2\u00b3\u00b9\u2070-\u209f]", "", text)

    # Remove zero-width and invisible formatting characters
    text = re.sub(r"[\u200b-\u200f\u200d\u202a-\u202e\u2060\ufeff\u00ad]", "", text)

    # Collapse repeated punctuation (.. → ., ,,, → ,, !!! → !, etc.)
    text = re.sub(r'([.!?,;:~\-]){2,}', r'\1', text)

    # Remove standalone repeated characters (e.g "aaaa", "wwwww")
    text = re.sub(r'\b(\w)\1{3,}\b', r'\1', text)

    # Collapse multiple spaces into one and strip
    text = re.sub(r"\s+", " ", text).strip()

    # Lowercase
    text = text.lower()

    return text

def _demojize_enclosed_letters(ch: str) -> str:
    """
    Convert enclosed/squared/circled latin letters to plain letters.
    Examples: 🆁 -> R, 🅰 -> A, ⓐ -> a
    """
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return ch

    patterns = [
        "SQUARED LATIN CAPITAL LETTER ",
        "NEGATIVE SQUARED LATIN CAPITAL LETTER ",
        "CIRCLED LATIN CAPITAL LETTER ",
        "LATIN CAPITAL LETTER ",  # (rarely needed, but harmless)
        "SQUARED LATIN SMALL LETTER ",
        "NEGATIVE SQUARED LATIN SMALL LETTER ",
        "CIRCLED LATIN SMALL LETTER ",
        "LATIN SMALL LETTER ",
    ]

    for p in patterns:
        if name.startswith(p):
            letter = name[len(p):]  # last part should be like "A", "B", ...
            if len(letter) == 1 and "A" <= letter <= "Z":
                # preserve case depending on "CAPITAL"/"SMALL"
                return letter if "CAPITAL" in name else letter.lower()

    return ch


def _normalize_text(text: str, max_repeat: int = 2) -> str:
    # First try Unicode normalization
    text = unicodedata.normalize("NFKC", text)

    # Fallback: convert squared/circled/enclosed latin letters using unicode names
    text = "".join(_demojize_enclosed_letters(ch) for ch in text)

    # Remove combining marks (accent/diacritics)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    # Collapse repeated characters
    text = re.sub(r"(.)\1{" + str(max_repeat) + r",}", r"\1" * max_repeat, text)

    return text
