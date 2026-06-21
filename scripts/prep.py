#!/usr/bin/env python3
import os, re, json, glob

GAME = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization V/Civilization V.app/Contents/Assets/Assets")
WORK = os.path.expanduser("~/civ5_rus_work")
IN   = os.path.join(WORK, "in")
os.makedirs(IN, exist_ok=True)

CHUNK_BYTES = 22000

# collect all en_US text files under DLC
files = []
for d in glob.glob(GAME + "/DLC/**/Text/en_US", recursive=True):
    for f in glob.glob(d + "/*.xml") + glob.glob(d + "/*.XML"):
        files.append(f)
files = sorted(set(files))

row_re = re.compile(r"<Row\b.*?</Row>", re.DOTALL)

manifest = []   # {target, src, chunks:[ids], textcount}
jid = 0
skipped = []
for src in files:
    with open(src, "r", encoding="utf-8", errors="replace") as fh:
        data = fh.read()
    rows = row_re.findall(data)
    textcount = data.count("<Text")
    if not rows:
        skipped.append(src)
        continue
    target = src.replace("/en_US/", "/RU_RU/")
    # group rows into chunks by byte size
    chunks_ids = []
    cur = []
    cursz = 0
    def flush():
        global jid
        if not cur:
            return
        cid = f"{jid:04d}"
        with open(os.path.join(IN, cid + ".xml"), "w", encoding="utf-8") as out:
            out.write("\n".join(cur))
        chunks_ids.append(cid)
        jid += 1
    for r in rows:
        rsz = len(r.encode("utf-8"))
        if cur and cursz + rsz > CHUNK_BYTES:
            flush(); cur = []; cursz = 0
        cur.append(r); cursz += rsz
    flush()
    manifest.append({"target": target, "src": src, "chunks": chunks_ids, "textcount": textcount})

with open(os.path.join(WORK, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump({"files": manifest, "total_chunks": jid}, fh, ensure_ascii=False, indent=1)

print(f"Файлов обработано: {len(manifest)}")
print(f"Пропущено (без <Row>): {len(skipped)}")
for s in skipped[:10]:
    print("  skip:", s.split('/DLC/')[-1])
print(f"Всего чанков для перевода: {jid}")
