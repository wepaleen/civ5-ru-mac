#!/usr/bin/env python3
import os, json, glob, subprocess, re

WORK = os.path.expanduser("~/civ5_rus_work")
OUT  = os.path.join(WORK, "out")

with open(os.path.join(WORK, "manifest.json"), encoding="utf-8") as fh:
    manifest = json.load(fh)

HEADER = '<?xml version="1.0" encoding="utf-8"?>\n<!-- Русская локализация -->\n<GameData>\n\t<Language_RU_RU>\n'
FOOTER = '\n\t</Language_RU_RU>\n</GameData>\n'

written = 0
mismatch = []
missing  = []
invalid  = []

for entry in manifest["files"]:
    target = entry["target"]
    parts = []
    miss = False
    for cid in entry["chunks"]:
        p = os.path.join(OUT, cid + ".xml")
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            miss = True
            break
        with open(p, encoding="utf-8") as fh:
            parts.append(fh.read().strip())
    if miss:
        missing.append((target, entry["chunks"]))
        continue
    body = "\n".join(parts)
    content = HEADER + body + FOOTER
    # validate text count
    out_textcount = content.count("<Text")
    if out_textcount != entry["textcount"]:
        mismatch.append((target.split("/DLC/")[-1], entry["textcount"], out_textcount))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as fh:
        fh.write(content)
    # xml validity
    r = subprocess.run(["xmllint", "--noout", target], capture_output=True)
    if r.returncode != 0:
        invalid.append((target.split("/DLC/")[-1], r.stderr.decode()[:200]))
    written += 1

print(f"=== СБОРКА ===")
print(f"Записано RU_RU файлов: {written}/{len(manifest['files'])}")
print(f"Незавершённых (нет чанков перевода): {len(missing)}")
for t, ch in missing[:20]:
    print(f"  MISSING: {t.split('/DLC/')[-1]}  чанки={ch}")
print(f"Несовпадение числа записей: {len(mismatch)}")
for t, a, b in mismatch[:30]:
    print(f"  COUNT: {t}  ориг={a} перевод={b}")
print(f"Невалидный XML: {len(invalid)}")
for t, e in invalid[:30]:
    print(f"  XMLERR: {t}  {e}")
