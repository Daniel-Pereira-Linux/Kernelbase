#!/usr/bin/env python3
"""initramfs mínima do laboratório: busybox (musl) + 4 módulos para montar a raiz 9p.
Uso: mkinitrd.py <arvore-alpine> <dir-modulos-descompactados> <saida.gz>"""
import os, sys, gzip, stat
alpine, moddir, out = sys.argv[1:4]
MODS = ["kernel/fs/netfs/netfs.ko", "kernel/net/9p/9pnet.ko", "kernel/fs/9p/9p.ko", "kernel/net/9p/9pnet_virtio.ko"]
INIT = r'''#!/bin/busybox sh
B=/bin/busybox
$B mount -t devtmpfs devtmpfs /dev
$B mount -t proc proc /proc
$B mount -t sysfs sysfs /sys
for m in netfs 9pnet 9p 9pnet_virtio; do $B insmod /m/$m.ko; done
i=0
until $B mount -t 9p -o rw,trans=virtio,version=9p2000.L,cache=loose,msize=512000 host9p /newroot; do
  i=$((i+1)); [ $i -gt 50 ] && { echo "kernelbase: nao consegui montar a raiz"; exec $B sh; }
  $B usleep 100000
done
for d in dev proc sys; do $B mount --move /$d /newroot/$d; done
exec $B switch_root /newroot /usr/sbin/kb-init
'''
entries = []  # (name, mode, data)
def d(name): entries.append((name, stat.S_IFDIR | 0o755, b""))
for n in ("bin", "dev", "proc", "sys", "newroot", "m", "lib"): d(n)
entries.append(("bin/busybox", stat.S_IFREG | 0o755, open(os.path.join(alpine, "bin/busybox"), "rb").read()))
entries.append(("lib/ld-musl-i386.so.1", stat.S_IFREG | 0o755, open(os.path.join(alpine, "lib/ld-musl-i386.so.1"), "rb").read()))
entries.append(("init", stat.S_IFREG | 0o755, INIT.encode()))
for m in MODS:
    entries.append(("m/" + os.path.basename(m), stat.S_IFREG | 0o644, open(os.path.join(moddir, m), "rb").read()))
def hdr(ino, name, mode, size, dev_major=0, dev_minor=0):
    nm = name.encode() + b"\0"
    h = b"070701" + b"".join(b"%08X" % v for v in (ino, mode, 0, 0, 1, 0, size, 0, 0, dev_major, dev_minor, len(nm), 0))
    data = h + nm
    return data + b"\0" * ((4 - len(data) % 4) % 4)
buf = bytearray()
ino = 1
# /dev/console para o kernel ter saída antes do devtmpfs
buf += hdr(ino, "dev/console", stat.S_IFCHR | 0o600, 0, 0, 0)
for name, mode, data in [entries[1]] + entries:  # garante dev antes
    pass
buf = bytearray()
for name, mode, data in entries:
    buf += hdr(ino, name, mode, len(data)) + data + b"\0" * ((4 - len(data) % 4) % 4); ino += 1
    if name == "dev":
        # nó de console (5,1)
        nm = b"dev/console\0"
        h = b"070701" + b"".join(b"%08X" % v for v in (ino, stat.S_IFCHR | 0o600, 0, 0, 1, 0, 0, 0, 0, 5, 1, len(nm), 0))
        x = h + nm; buf += x + b"\0" * ((4 - len(x) % 4) % 4); ino += 1
buf += hdr(ino, "TRAILER!!!", 0, 0)
with gzip.GzipFile(out, "wb", compresslevel=9, mtime=0) as f:
    f.write(bytes(buf))
print("initramfs:", os.path.getsize(out), "bytes")
