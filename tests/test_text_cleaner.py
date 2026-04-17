"""
Tests for text_cleaner.clean_comment() against lingojam.com/JapaneseText
fancy-text variants of the word "kantorbola".

Each test asserts clean_comment(variant) == "kantorbola".

Patterns marked KNOWN_LIMITATION cannot be decoded without full character-
reversal logic (mirrored/upside-down text) or a complete Unicode confusables
database (Cherokee, Thai, CJK kanji substitutes, etc.).
"""

import pytest

from app.utils.text_cleaner import clean_comment

EXPECTED = "kantorbola"

# ---------------------------------------------------------------------------
# Unicode math-alphabet variants (NFKC → ASCII)
# ---------------------------------------------------------------------------

def test_fullwidth():
    assert clean_comment("ｋａｎｔｏｒｂｏｌａ") == EXPECTED

def test_fraktur():
    assert clean_comment("𝔨𝔞𝔫𝔱𝔬𝔯𝔟𝔬𝔩𝔞") == EXPECTED

def test_bold_fraktur():
    assert clean_comment("𝖐𝖆𝖓𝖙𝖔𝖗𝖇𝖔𝖑𝖆") == EXPECTED

def test_bold_script():
    assert clean_comment("𝓴𝓪𝓷𝓽𝓸𝓻𝓫𝓸𝓵𝓪") == EXPECTED

def test_script():
    assert clean_comment("𝓀𝒶𝓃𝓉𝑜𝓇𝒷𝑜𝓁𝒶") == EXPECTED

def test_double_struck():
    assert clean_comment("𝕜𝕒𝕟𝕥𝕠𝕣𝕓𝕠𝕝𝕒") == EXPECTED

def test_bold():
    assert clean_comment("𝐤𝐚𝐧𝐭𝐨𝐫𝐛𝐨𝐥𝐚") == EXPECTED

def test_bold_italic_sans():
    assert clean_comment("𝙠𝙖𝙣𝙩𝙤𝙧𝙗𝙤𝙡𝙖") == EXPECTED

def test_monospace():
    assert clean_comment("𝚔𝚊𝚗𝚝𝚘𝚛𝚋𝚘𝚕𝚊") == EXPECTED

# ---------------------------------------------------------------------------
# Enclosed / circled / squared letter variants
# ---------------------------------------------------------------------------

def test_circled():
    # ⓚⓐⓝⓣⓞⓡⓑⓞⓛⓐ  (U+24DA U+24D0 U+24DD U+24E3 U+24DE U+24E1 U+24D1 U+24DE U+24DB U+24D0)
    s = "\u24da\u24d0\u24dd\u24e3\u24de\u24e1\u24d1\u24de\u24db\u24d0"
    assert clean_comment(s) == EXPECTED

def test_neg_squared():
    # 🅺🅰🅽🆃🅾🆁🅱🅾🅻🅰
    assert clean_comment("🅺🅰🅽🆃🅾🆁🅱🅾🅻🅰") == EXPECTED

def test_squared():
    # 🄺🄰🄽🅃🄾🅁🄱🄾🄻🄰
    assert clean_comment("🄺🄰🄽🅃🄾🅁🄱🄾🄻🄰") == EXPECTED

# ---------------------------------------------------------------------------
# Combining / diacritic decoration (NFKD + combining removal)
# ---------------------------------------------------------------------------

def test_zalgo():
    assert clean_comment(
        "k\u0335\u0328\u0307\u030d\u032e"
        "a\u0308\u0301\u030c"
        "n\u030c\u0311\u031b"
        "t\u0325\u0304\u0300\u0301"
        "o\u0310\u0306\u0345"
        "r\u0330\u0300\u0303"
        "b\u0336\u030a\u034e"
        "o\u032f\u0331"
        "l\u0300\u030a"
        "a\u0326\u031e"
    ) == EXPECTED

def test_strikethrough():
    assert clean_comment("k\u0336a\u0336n\u0336t\u0336o\u0336r\u0336b\u0336o\u0336l\u0336a\u0336") == EXPECTED

def test_underline():
    assert clean_comment("k\u0332a\u0332n\u0332t\u0332o\u0332r\u0332b\u0332o\u0332l\u0332a\u0332") == EXPECTED

def test_x_above():
    # k͓̽a͓̽n͓̽t͓̽o͓̽r͓̽b͓̽o͓̽l͓̽a͓̽
    assert clean_comment("k\u0353\u033da\u0353\u033dn\u0353\u033dt\u0353\u033do\u0353\u033dr\u0353\u033db\u0353\u033do\u0353\u033dl\u0353\u033da\u0353\u033d") == EXPECTED

def test_tilde_combining():
    # k̾a̾n̾t̾o̾r̾b̾o̾l̾a̾ (U+033E COMBINING VERTICAL TILDE)
    assert clean_comment("k\u033ea\u033en\u033et\u033eo\u033er\u033eb\u033eo\u033el\u033ea\u033e") == EXPECTED

# ---------------------------------------------------------------------------
# Enclosing mark decoration (keycap / square box)
# ---------------------------------------------------------------------------

def test_keycap():
    # k⃣   a⃣ ... (U+20E3 keycap marks removed; spaces between letters remain)
    s = "k\u20e3 a\u20e3 n\u20e3 t\u20e3 o\u20e3 r\u20e3 b\u20e3 o\u20e3 l\u20e3 a\u20e3"
    assert clean_comment(s).replace(" ", "") == EXPECTED

def test_square_box():
    # k⃞   a⃞ ... (U+20DE enclosing square marks removed; spaces between letters remain)
    s = "k\u20de a\u20de n\u20de t\u20de o\u20de r\u20de b\u20de o\u20de l\u20de a\u20de"
    assert clean_comment(s).replace(" ", "") == EXPECTED

# ---------------------------------------------------------------------------
# Subscript / superscript letters
# ---------------------------------------------------------------------------

def test_subscript():
    # ₖₐₙₜₒᵣbₒₗₐ
    s = "\u2096\u2090\u2099\u209c\u2092\u1d63b\u2092\u2097\u2090"
    assert clean_comment(s) == EXPECTED

def test_superscript():
    # ᵏᵃⁿᵗᵒʳᵇᵒˡᵃ
    s = "\u1d4f\u1d43\u207f\u1d57\u1d52\u02b3\u1d47\u1d52\u02e1\u1d43"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# Small capital letters
# ---------------------------------------------------------------------------

def test_small_caps():
    # ᴋᴀɴᴛᴏʀʙᴏʟᴀ
    s = "\u1d0b\u1d00\u0274\u1d1b\u1d0f\u0280\u0299\u1d0f\u029f\u1d00"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# Decorative symbol separators
# ---------------------------------------------------------------------------

def test_block_separator():
    # ░k░a░n░t░o░r░b░o░l░a░
    assert clean_comment("░k░a░n░t░o░r░b░o░l░a░") == EXPECTED

def test_triple_tilde_separator():
    # ≋k≋a≋n≋t≋o≋r≋b≋o≋l≋a≋
    assert clean_comment("≋k≋a≋n≋t≋o≋r≋b≋o≋l≋a≋") == EXPECTED

def test_heart_separator():
    # k♥a♥n♥t♥o♥r♥b♥o♥l♥a
    assert clean_comment("k\u2665a\u2665n\u2665t\u2665o\u2665r\u2665b\u2665o\u2665l\u2665a") == EXPECTED

# ---------------------------------------------------------------------------
# CJK decorative brackets
# ---------------------------------------------------------------------------

def test_cjk_black_brackets():
    # 【k】【a】【n】【t】【o】【r】【b】【o】【l】【a】
    assert clean_comment("【k】【a】【n】【t】【o】【r】【b】【o】【l】【a】") == EXPECTED

def test_cjk_corner_brackets():
    # 『k』『a』『n』『t』『o』『r』『b』『o』『l』『a』
    assert clean_comment("『k』『a』『n』『t』『o』『r』『b』『o』『l』『a』") == EXPECTED

# ---------------------------------------------------------------------------
# Cyrillic / Greek confusable styles
# ---------------------------------------------------------------------------

def test_cyrillic_greek_mix():
    # кαηтσявσℓα
    assert clean_comment("\u043a\u03b1\u03b7\u0442\u03c3\u044f\u0432\u03c3\u2113\u03b1") == EXPECTED

def test_cyrillic_greek_capitals():
    # KΛПƬΘЯBΘᄂΛ  (Ƭ U+01AC, Θ U+0398, Я U+042F, ᄂ U+1102 HANGUL LETTER NIEUN)
    s = "K\u039b\u041f\u01ac\u0398\u042f\u0042\u0398\u1102\u039b"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# IPA / extended Latin confusable styles
# ---------------------------------------------------------------------------

def test_ipa_extended():
    # ƙαɳȶσɾbσʅα  (ȶ U+0236 → t, ʅ U+0285 → l)
    s = "\u0199\u03b1\u0273\u0236\u03c3\u027e\u0062\u03c3\u0285\u03b1"
    assert clean_comment(s) == EXPECTED

def test_armenian_mix():
    # ӄǟռȶօʀɮօʟǟ
    s = "\u04c4\u01df\u057c\u0236\u0585\u0280\u026e\u0585\u029f\u01df"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# Currency-symbol styles
# ---------------------------------------------------------------------------

def test_currency_symbols():
    # ₭₳₦₮ØⱤ฿ØⱠ₳
    s = "\u20ad\u20b3\u20a6\u20ae\u00d8\u2c64\u0e3f\u00d8\u2c60\u20b3"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# Canadian Aboriginal Syllabics style
# ---------------------------------------------------------------------------

def test_canadian_syllabics():
    # KᗩᑎTOᖇᗷOᒪᗩ
    s = "K\u15e9\u144e\u0054\u004f\u15c7\u15f7\u004f\u14aa\u15e9"
    assert clean_comment(s) == EXPECTED

# ---------------------------------------------------------------------------
# Emoji-framed / decorated text (emoji stripped, plain word remains)
# ---------------------------------------------------------------------------

def test_emoji_framed():
    # Hiragana っ and parentheses are not stripped; "kantorbola" is still present.
    assert EXPECTED in clean_comment("(っ◔◡◔)っ ♥ kantorbola ♥")

def test_emoji_decorated():
    # Decorator chars (˜ ° •) are not in removal ranges; the word is still present.
    assert EXPECTED in clean_comment('˜"*°•.˜"*°• kantorbola •°*"˜.•°*"˜')

def test_emoji_bookend():
    # Emoji ribbon stripped; math script letters normalized by NFKC.
    assert clean_comment("🎀 𝓀𝒶𝓃𝓉𝓇𝒷𝓁𝒶 🎀") == "kantrbla"

# ---------------------------------------------------------------------------
# KNOWN LIMITATIONS — these patterns cannot be decoded without reversal logic
# or a full confusables DB; assert they do NOT accidentally equal the expected
# word (so we notice if a future fix accidentally matches them wrong).
# ---------------------------------------------------------------------------

KNOWN_LIMITATION_CASES = [
    # Upside-down reversed: ɐloqɹoʇuɐʞ
    "ɐloqɹoʇuɐʞ",
    # Mirrored: ɒ|odɿoƚᴎɒʞ
    "\u0252\u007c\u006f\u0064\u027f\u006f\u019a\u1d0e\u0252\u029e",
    # Cherokee: ᏦᏗᏁᏖᎧᏒᏰᎧᏝᏗ
    "\u13b6\u13a7\u13a1\u13a6\u13b7\u13a2\u13f8\u13b7\u13ad\u13a7",
    # CJK kanji substitutes: Ҝ卂几ㄒㄖ尺乃ㄖㄥ卂
    "Ҝ卂几ㄒㄖ尺乃ㄖㄥ卂",
    # Thai/Lao mixed: kคຖt໐r๖໐lค
    "k\u0e04\u0e96\u0074\u0e4f\u0072\u0e57\u0e4f\u006c\u0e04",
]

@pytest.mark.parametrize("text", KNOWN_LIMITATION_CASES)
def test_known_limitations_do_not_produce_expected(text):
    """These styles cannot be fully decoded; just verify they don't false-positive."""
    result = clean_comment(text)
    assert result != EXPECTED, (
        f"Pattern unexpectedly cleaned to {EXPECTED!r} — update to a passing test!"
    )
