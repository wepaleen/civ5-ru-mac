#!/usr/bin/env python3
"""Normalize RU_RU text to glyphs the Civ V Mac font atlas can render.

The Cyrillic font shipped with the russifier covers А-я (U+0410..U+044F) plus
ASCII, but NOT ё/Ё, « », em-dash, accented Latin, etc. — those render as gaps.
This rewrites all RU_RU XML to font-safe equivalents.

Usage: python3 normalize.py "/path/to/Civilization V.app/Contents/Assets/Assets"
"""
import os, sys, glob, unicodedata, collections

if len(sys.argv) < 2:
    sys.exit("usage: normalize.py <ASSETS dir (…/Contents/Assets/Assets)>")
A = sys.argv[1]

REPL = {
    'Ё': 'Е', 'ё': 'е',
    '«': '"', '»': '"', '“': '"', '”': '"', '„': '"',
    '‘': "'", '’': "'", '‚': "'",
    '—': '-', '–': '-', '‒': '-',
    '…': '...', '№': 'N',
    ' ': ' ', ' ': ' ', ' ': ' ', '﻿': '',
}
MANUAL = {
    'ø': 'o', 'Ø': 'O', 'ß': 'ss', 'đ': 'd', 'Đ': 'D', 'ł': 'l', 'Ł': 'L',
    'þ': 'th', 'Þ': 'Th', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
    'ð': 'd', 'Ð': 'D', '©': '(c)', '®': '(r)', '™': '(tm)',
    '°': '', '−': '-', '×': 'x', '÷': '/', '•': '*',
}

def supported(ch):
    o = ord(ch)
    return (0x20 <= o <= 0x7E) or (0x0410 <= o <= 0x044F) or ch in '\n\r\t'

def fix_char(ch):
    if supported(ch):
        return ch
    if ch in REPL:
        return REPL[ch]
    if ch in MANUAL:
        return MANUAL[ch]
    base = ''.join(c for c in unicodedata.normalize('NFKD', ch) if not unicodedata.combining(c))
    if base and all(supported(c) for c in base):
        return base
    return ''

files = []
for d in glob.glob(A + "/Gameplay/XML/NewText/RU_RU") + glob.glob(A + "/DLC/**/Text/RU_RU", recursive=True):
    files += glob.glob(d + "/*.xml") + glob.glob(d + "/*.XML")

changed = 0
remaining = collections.Counter()
for f in sorted(set(files)):
    data = open(f, encoding="utf-8").read()
    out = ''.join(fix_char(c) for c in data)
    if out != data:
        open(f, "w", encoding="utf-8").write(out)
        changed += 1
    for ch in out:
        if not supported(ch):
            remaining[ch] += 1

print(f"RU_RU файлов: {len(set(files))}, изменено: {changed}, остаточных непокрытых символов: {len(remaining)}")
for ch, n in remaining.most_common(15):
    print(f"  U+{ord(ch):04X} {ch!r} x{n}")
