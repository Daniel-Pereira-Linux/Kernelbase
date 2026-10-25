#!/usr/bin/env python3
"""Gera <saida>/<nome>-fs.json e preenche o diretório flat compartilhado com
arquivos .bin.zst (nome = 10 primeiros hex do sha256 do conteúdo original).

Uso: mkflat.py <tree> <nome> <dir-saida> <helper-chroot>
"""
import os, sys, json, stat, hashlib, shutil, subprocess

tree, name, outdir, helper = sys.argv[1:5]
flat = os.path.join(outdir, "flat")
os.makedirs(flat, exist_ok=True)
stage_rel = "kbstage"
stage = os.path.join(helper, stage_rel)
if os.path.exists(stage):
    shutil.rmtree(stage)
os.makedirs(stage)

HASH_LENGTH = 10
EXCLUDE = {"/usr/share/doc", "/proc", "/sys", "/dev", "/run", "/tmp", "/var/cache/apt", "/var/cache/yum",
           "/var/lib/apt/lists", "/var/log/journal"}
KEEP_LOCALE = ("pt", "pt_BR", "en", "en_US", "en_GB", "locale.alias")

def excluded(rel):
    if rel in EXCLUDE:
        return True
    if rel.startswith("/usr/share/locale/"):
        part = rel.split("/")[4]
        return part not in KEEP_LOCALE
    return False

total = 0
new_files = 0
seen = {}

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def node(full, rel, st):
    global total, new_files
    obj = [os.path.basename(rel) if rel != "/" else "", st.st_size, int(st.st_mtime), int(st.st_mode), st.st_uid, st.st_gid, None]
    mode = st.st_mode
    if stat.S_ISLNK(mode):
        obj[6] = os.readlink(full)
    elif stat.S_ISDIR(mode):
        kids = []
        for n in sorted(os.listdir(full)):
            r = (rel.rstrip("/") + "/" + n)
            if excluded(r):
                # mantém o diretório vazio (ex.: /proc), sem conteúdo
                f2 = os.path.join(full, n)
                s2 = os.lstat(f2)
                if stat.S_ISDIR(s2.st_mode):
                    kids.append([n, 0, int(s2.st_mtime), int(s2.st_mode), s2.st_uid, s2.st_gid, []])
                continue
            f2 = os.path.join(full, n)
            s2 = os.lstat(f2)
            if stat.S_ISREG(s2.st_mode) or stat.S_ISDIR(s2.st_mode) or stat.S_ISLNK(s2.st_mode):
                kids.append(node(f2, r, s2))
        obj[6] = kids
        obj[1] = 0
    elif stat.S_ISREG(mode):
        total += st.st_size
        key = (st.st_dev, st.st_ino)
        if key in seen:
            h = seen[key]
        else:
            h = sha(full)[:HASH_LENGTH]
            seen[key] = h
        fname = h + ".bin.zst"
        obj[6] = fname
        if not os.path.exists(os.path.join(flat, fname)) and not os.path.exists(os.path.join(stage, h + ".bin")):
            shutil.copyfile(full, os.path.join(stage, h + ".bin"))
            new_files += 1
    return obj

root_st = os.lstat(tree)
root = node(tree, "/", root_st)[6]
with open(os.path.join(outdir, name + "-fs.json"), "w") as f:
    json.dump({"fsroot": root, "version": 3, "size": total}, f, separators=(",", ":"))

# compacta no chroot auxiliar (zstd i386), depois move para o flat
if new_files:
    subprocess.run(["chroot", helper, "/bin/sh", "-c",
                    "cd /%s && find . -name '*.bin' -print0 | xargs -0 -n 200 zstd -q -T2 -12 --rm" % stage_rel],
                   check=True)
    for f in os.listdir(stage):
        shutil.move(os.path.join(stage, f), os.path.join(flat, f))
shutil.rmtree(stage)
print("%s: %d MB de arquivos, %d arquivos novos no flat" % (name, total // (1 << 20), new_files))
