"""Utility functions for cleaning comment text."""

import re

import emoji


def clean_comment(text: str) -> str:
    """
    Clean a comment string:
    1. Remove all emojis (using the emoji library).
    2. Remove superscripts/subscripts (², ³, etc.).
    3. Collapse whitespace and convert to lowercase.

    Examples:
        >>> clean_comment("Bang windah kamu kok gak main 😢😢😢")
        'bang windah kamu kok gak main'
        >>> clean_comment("Vlognya bikin kangen! 💕𝐌𝐎𝐍𝐀𝟒𝐃🟣 bikin hidup!")
        'vlognya bikin kangen! 𝐌𝐎𝐍𝐀𝟒𝐃 bikin hidup!'
    """
    if not text:
        return ""

    # 1. Remove all emojis detected by the emoji library
    text = emoji.replace_emoji(text, replace="")

    # 2. Remove remaining emoji/symbol unicode ranges not caught by the library
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

    # 3. Remove superscripts and subscripts (², ³, ¹, ⁰-⁹, ₀-₉, etc.)
    text = re.sub(r"[\u00b2\u00b3\u00b9\u2070-\u209f]", "", text)

    # 4. Remove zero-width and invisible formatting characters
    text = re.sub(r"[\u200b-\u200f\u200d\u202a-\u202e\u2060\ufeff\u00ad]", "", text)

    # 5. Collapse repeated punctuation (... → ., ,,, → ,, !!! → !, etc.)
    text = re.sub(r'([.!?,;:~\-]){2,}', r'\1', text)

    # 6. Remove standalone repeated characters (e.g. "aaaa", "wwwww")
    text = re.sub(r'\b(\w)\1{3,}\b', r'\1', text)

    # 7. Collapse multiple spaces into one and strip
    text = re.sub(r"\s+", " ", text).strip()

    # 8. Lowercase
    text = text.lower()

    return text
