#!/usr/bin/env python3
"""Monta uma imagem de laboratório (Debian 12 ou CentOS 7, i386) para o v86.

Uso: build_image.py <debian|centos> <rootfs-base> <alpine-tree> <saida-tree>

- copia o rootfs base para <saida-tree>
- coloca kernel e initramfs do Alpine (linux-virt) em /boot e os módulos em /lib/modules
- instala /opt/kernelbase com musl + ferramentas que faltam (vim, less, man, procps...)
  e o busybox para o resto, sem sobrescrever o que a distro já tem
- instala o init do laboratório (/sbin/kb-init), motd, prompt e o comando kb-ajuda
"""
import os, sys, shutil, stat, subprocess, glob

distro, base, alpine, out = sys.argv[1:5]
assert distro in ("debian", "centos")

def sh(*a):
    subprocess.run(a, check=True)

if os.path.exists(out):
    shutil.rmtree(out)
sh("cp", "-a", base, out)

def P(p):  # caminho dentro da imagem
    return os.path.join(out, p.lstrip("/"))

def A(p):  # caminho dentro do Alpine
    return os.path.join(alpine, p.lstrip("/"))

def exists_in_target(cmd):
    for d in ("usr/local/bin", "usr/local/sbin", "usr/bin", "usr/sbin", "bin", "sbin"):
        if os.path.lexists(P(d + "/" + cmd)):
            return True
    return False

def write(path, text, mode=0o644):
    full = P(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(full, mode)

# ---------- kernel, initramfs e módulos ----------
os.makedirs(P("/boot"), exist_ok=True)
for f in ("vmlinuz-virt", "initramfs-virt"):
    shutil.copy2(A("/boot/" + f), P("/boot/" + f))
mods = glob.glob(A("/lib/modules/*"))
assert len(mods) == 1
kver = os.path.basename(mods[0])
dst_mod = P("/usr/lib/modules/" + kver) if os.path.islink(P("/lib")) else P("/lib/modules/" + kver)
os.makedirs(os.path.dirname(dst_mod), exist_ok=True)
sh("cp", "-a", mods[0], dst_mod)
# módulos descompactados: o kmod do Debian não lê .ko.gz
for root_, dirs_, files_ in os.walk(dst_mod):
    for f_ in files_:
        if f_.endswith(".ko.gz"):
            sh("gunzip", "-f", os.path.join(root_, f_))

_KVER_FOR_DEPMOD = kver
# ---------- musl + ferramentas do Alpine em /opt/kernelbase ----------
KB = P("/opt/kernelbase")
os.makedirs(KB + "/bin", exist_ok=True)
os.makedirs(KB + "/lib", exist_ok=True)
shutil.copy2(A("/lib/ld-musl-i386.so.1"), P("/lib/ld-musl-i386.so.1"))
# a distro é usr-merged: /lib -> usr/lib, então o loader fica em /usr/lib também
for libdir in ("/lib", "/usr/lib"):
    for f in glob.glob(A(libdir) + "/*.so*"):
        name = os.path.basename(f)
        dst = KB + "/lib/" + name
        if os.path.islink(f):
            if not os.path.lexists(dst):
                t = os.readlink(f)
                os.symlink(os.path.basename(t), dst)
        else:
            shutil.copy2(f, dst)
if not os.path.lexists(KB + "/lib/libc.musl-x86.so.1"):
    os.symlink("/lib/ld-musl-i386.so.1", KB + "/lib/libc.musl-x86.so.1")
# o musl lê só este caminho: assim ele nunca carrega as bibliotecas glibc da distro
write("/etc/ld-musl-i386.path", "/opt/kernelbase/lib\n")

shutil.copy2(A("/bin/busybox"), KB + "/bin/busybox")

# ferramentas "de verdade" do Alpine (preferidas ao busybox quando existirem)
REAL = {
    # procps-ng
    "ps": "/bin/ps", "top": "/usr/bin/top", "free": "/usr/bin/free", "pgrep": "/usr/bin/pgrep",
    "pkill": "/usr/bin/pkill", "pidof": "/bin/pidof", "uptime": "/usr/bin/uptime", "w": "/usr/bin/w",
    "watch": "/usr/bin/watch", "vmstat": "/usr/bin/vmstat", "pmap": "/usr/bin/pmap",
    "pwdx": "/usr/bin/pwdx", "tload": "/usr/bin/tload", "slabtop": "/usr/bin/slabtop",
    "kill": "/bin/kill", "sysctl": "/sbin/sysctl",
    # editores, paginação e manuais
    "vim": "/usr/bin/vim", "vimtutor": "/usr/bin/vimtutor", "xxd": "/usr/bin/xxd",
    "less": "/usr/bin/less", "man": "/usr/bin/man", "mandoc": "/usr/bin/mandoc",
    "apropos": "/usr/bin/apropos", "whatis": "/usr/bin/whatis",
    # kmod
    "kmod": "/bin/kmod", "lsmod": "/sbin/lsmod", "modprobe": "/sbin/modprobe", "modinfo": "/sbin/modinfo",
    "insmod": "/sbin/insmod", "rmmod": "/sbin/rmmod", "depmod": "/sbin/depmod",
    # e2fsprogs e discos
    "mke2fs": "/sbin/mke2fs", "mkfs.ext2": "/sbin/mkfs.ext2", "mkfs.ext3": "/sbin/mkfs.ext3",
    "mkfs.ext4": "/sbin/mkfs.ext4", "e2fsck": "/sbin/e2fsck", "fsck.ext4": "/sbin/fsck.ext4",
    "fsck.ext2": "/sbin/fsck.ext2", "fsck.ext3": "/sbin/fsck.ext3",
    "tune2fs": "/sbin/tune2fs", "dumpe2fs": "/sbin/dumpe2fs", "resize2fs": "/sbin/resize2fs",
    "debugfs": "/sbin/debugfs", "e2label": "/sbin/e2label", "badblocks": "/sbin/badblocks",
    "fdisk": "/sbin/fdisk", "sfdisk": "/sbin/sfdisk", "cfdisk": "/sbin/cfdisk",
    "lsblk": "/bin/lsblk", "lscpu": "/usr/bin/lscpu", "hexdump": "/usr/bin/hexdump",
}
BUSYBOX = ["ip", "ifconfig", "route", "netstat", "ping", "ping6", "traceroute", "nslookup", "nc",
           "wget", "arp", "crontab", "crond", "bzip2", "bunzip2", "bzcat", "unxz", "xzcat", "lzma",
           "cpio", "which", "killall", "lsof", "last", "tree", "syslogd", "klogd", "logread",
           "hwclock", "lsusb", "fuser", "pstree", "nproc", "strings", "unzip", "bc", "dc",
           "uudecode", "uuencode", "iostat", "mpstat", "ipcalc", "watch", "time", "timeout",
           "hd"]

def copy_alpine_bin(src, name):
    """Copia um binário do Alpine (seguindo links) para /opt/kernelbase/bin/name."""
    real = A(src)
    if os.path.islink(real):
        t = os.readlink(real)
        tgt = os.path.normpath(os.path.join(os.path.dirname(src), t)) if not t.startswith("/") else t
        if os.path.basename(tgt) == "busybox":
            return "busybox"
        base_name = os.path.basename(tgt)
        if not os.path.exists(KB + "/bin/" + base_name):
            copy_alpine_bin(tgt, base_name)
        if base_name != name and not os.path.lexists(KB + "/bin/" + name):
            os.symlink(base_name, KB + "/bin/" + name)
        return "real"
    if not os.path.exists(real):
        return None
    shutil.copy2(real, KB + "/bin/" + name)
    return "real"

linked = []
def link(cmd, target_in_kb):
    dst = P("/usr/local/bin/" + cmd)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.lexists(dst):
        os.remove(dst)
    os.symlink("/opt/kernelbase/bin/" + target_in_kb, dst)
    linked.append(cmd)

# vim e man são úteis mesmo onde a distro tem um equivalente mínimo
ALWAYS = set()  # a distro já traz vim, less e man de verdade
for cmd, src in REAL.items():
    if exists_in_target(cmd) and cmd not in ALWAYS:
        continue
    r = copy_alpine_bin(src, cmd)
    if r == "real":
        link(cmd, cmd)
    elif r == "busybox":
        link(cmd, "busybox")
for cmd in BUSYBOX:
    if not exists_in_target(cmd):
        os.symlink("busybox", KB + "/bin/" + cmd) if not os.path.lexists(KB + "/bin/" + cmd) else None
        link(cmd, cmd)

# runtime do vim, terminfo do musl e páginas de manual
if not os.path.exists(P("/usr/share/vim")):
    sh("cp", "-a", A("/usr/share/vim"), P("/usr/share/vim"))
os.makedirs(P("/opt/kernelbase/share"), exist_ok=True)
sh("cp", "-a", A("/etc/terminfo"), P("/opt/kernelbase/share/terminfo"))
sh("cp", "-an", A("/usr/share/man") + "/.", P("/usr/share/man"))
for f in ("/etc/vim/vimrc",):
    if os.path.exists(A(f)) and not os.path.exists(P(f)):
        os.makedirs(os.path.dirname(P(f)), exist_ok=True)
        shutil.copy2(A(f), P(f))
write("/etc/vim/vimrc.local", "set nocompatible\nsyntax on\nset background=dark\nset ruler\nset showmode\n")

# ---------- init do laboratório ----------
HOST = "debian-lab" if distro == "debian" else "centos-lab"
write("/etc/hostname", HOST + "\n")
write("/sbin/kb-init" if not os.path.islink(P("/sbin")) else "/usr/sbin/kb-init", r'''#!/bin/bash
# KernelBase: init do laboratório (PID 1)
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export TERMINFO_DIRS=/etc/terminfo:/lib/terminfo:/usr/lib/terminfo:/usr/share/terminfo:/opt/kernelbase/share/terminfo
mountpoint -q /proc || mount -t proc proc /proc
mountpoint -q /sys || mount -t sysfs sysfs /sys
mountpoint -q /dev || mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts /dev/shm
ln -sfn /proc/self/fd /dev/fd; ln -sf /proc/self/fd/0 /dev/stdin; ln -sf /proc/self/fd/1 /dev/stdout; ln -sf /proc/self/fd/2 /dev/stderr
mountpoint -q /dev/pts || mount -t devpts devpts /dev/pts -o gid=5,mode=620
mountpoint -q /dev/shm || mount -t tmpfs tmpfs /dev/shm
mountpoint -q /run || mount -t tmpfs tmpfs /run -o mode=755
mkdir -p /run/lock /var/log /var/spool/cron/crontabs /root/lab
mountpoint -q /tmp || mount -t tmpfs tmpfs /tmp -o mode=1777
hostname -F /etc/hostname
ip link set lo up 2>/dev/null
: > /var/run/utmp 2>/dev/null
depmod -a 2>/dev/null
# serviços reais da distro (sem systemd: iniciados direto aqui)
if command -v rsyslogd >/dev/null; then rsyslogd 2>/dev/null; else syslogd -O /var/log/messages 2>/dev/null; fi
if [ -x /usr/sbin/cron ]; then /usr/sbin/cron; elif [ -x /usr/sbin/crond ] && [ ! -L /usr/local/bin/crond ]; then /usr/sbin/crond; else crond -c /var/spool/cron/crontabs 2>/dev/null; fi
command -v atd >/dev/null && atd 2>/dev/null
mkdir -p /run/sshd /var/run/sshd
[ -x /usr/sbin/sshd ] && /usr/sbin/sshd -o ListenAddress=127.0.0.1 2>/dev/null
command -v updatedb >/dev/null && (updatedb 2>/dev/null &)
# shell de verificação das missões, na porta serial (o site conversa com ela)
stty -F /dev/ttyS0 115200 -echo 2>/dev/null
( while :; do
    echo "__KB_READY__" > /dev/ttyS0
    cat < /dev/ttyS0 | /bin/bash --noprofile --norc > /dev/ttyS0 2>&1
  done ) &
# terminal do aluno
while :; do
  setsid -c /bin/bash -l < /dev/tty1 > /dev/tty1 2>&1
  sleep 1
done
''', 0o755)

pkg = "dpkg -l | less     apt-cache show bash" if distro == "debian" else "rpm -qa | less     rpm -qi bash"
write("/etc/motd", """
  KernelBase - laboratório LPIC-1 - %s

  Esta máquina roda inteira no seu navegador. Nada sai daqui, e tudo
  é apagado quando o tempo do laboratório acaba.

  kb-ajuda      comandos para estudar, por objetivo do exame
  man <cmd>     manual de um comando (ex.: man ls)
  vimtutor      tutorial do vim
  %s

""" % ("Debian 12 (bookworm)" if distro == "debian" else "CentOS 7.9 (i386)", pkg))

write("/etc/profile.d/kernelbase.sh", r'''export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export TERMINFO_DIRS=/etc/terminfo:/lib/terminfo:/usr/lib/terminfo:/usr/share/terminfo:/opt/kernelbase/share/terminfo
export TERM=linux
export EDITOR=vim PAGER=less MANPAGER=less
export LESS=-R
alias ll='ls -l --color=auto'
alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='\[\e[1;36m\]\u@\h\[\e[0m\]:\[\e[1;35m\]\w\[\e[0m\]\$ '
[ -z "$KB_MOTD_SHOWN" ] && { clear; cat /etc/motd; export KB_MOTD_SHOWN=1; }
cd /root 2>/dev/null
''')
# CentOS só lê /etc/profile.d via /etc/profile (ok); Debian idem.

AJUDA_PKG = {
    "debian": "  102.4  dpkg -l   dpkg -L bash   dpkg -S /bin/ls   dpkg-query -W bash   apt-cache policy bash",
    "centos": "  102.5  rpm -qa   rpm -ql bash   rpm -qf /bin/ls   rpm -qi bash   yum list installed   yum history",
}[distro]
write("/usr/local/bin/kb-ajuda", r'''#!/bin/bash
cat <<'FIM' | less -R
KernelBase - comandos para praticar, por objetivo da LPIC-1

101  Arquitetura e boot
  101.1  lscpu   lsblk   lsmod   modinfo ext4   cat /proc/cpuinfo   cat /proc/meminfo   dmesg | less
  101.2  dmesg   cat /proc/cmdline   ls /boot
102  Instalar sistema e gerenciar pacotes
  102.1  lsblk   fdisk -l /dev/sda   cat /proc/partitions
  102.3  ldd /bin/ls   ldconfig -p | less   cat /etc/ld.so.conf
__PKG__
103  Comandos GNU e Unix
  103.1  pwd  cd  echo $PATH  type ls  history  env  export VAR=valor  man bash
  103.2  cat /etc/passwd | cut -d: -f1 | sort | uniq   wc -l   head  tail  tr  nl  od -c  split
  103.3  cp -a  mv  rm -r  mkdir -p  touch  file  find / -name passwd  tar czf  gzip  bzip2  dd
  103.4  ls /naoexiste 2> erro.txt   cmd > saida.txt   cmd >> saida.txt   cmd | tee arq   xargs
  103.5  ps aux   top   jobs   bg   fg   nohup   kill -15 PID   killall sleep   pgrep   free   uptime
  103.6  nice -n 10 sleep 999 &   renice 5 -p PID   ps -o pid,ni,cmd
  103.7  grep -E '^root|nologin$' /etc/passwd   grep -c   grep -v   sed 's/a/b/g'
  103.8  vim arquivo   (i insere, Esc volta, :wq salva e sai)   vimtutor
104  Discos, sistemas de arquivos e FHS
  104.1  fdisk /dev/sda   mkfs.ext4 /dev/sda1   mkswap   blkid
  104.2  df -h   du -sh /usr   e2fsck -f /dev/sda1   tune2fs -l /dev/sda1   dumpe2fs -h
  104.3  mkdir /mnt/dados   mount /dev/sda1 /mnt/dados   umount   cat /etc/fstab   findmnt
  104.5  chmod 750 arq   chmod u+s   chmod +t dir   chown aluno:aluno   umask   stat
  104.6  ln -s alvo link   ln alvo duro   ls -li
  104.7  find / -name '*.conf'   which ls   type ls   whereis ls   cat /etc/os-release
105  Shell e scripts
  105.1  alias   ~/.bashrc   /etc/profile   set   unset   source ~/.bashrc
  105.2  #!/bin/bash   if   for   while   read   test   $?   $1   chmod +x script.sh
107  Administrar o sistema
  107.1  useradd -m aluno   passwd aluno   usermod -aG grupo aluno   groupadd   id   /etc/shadow
  107.2  crontab -e   crontab -l   cat /etc/crontab
  107.3  date   echo $LANG   locale   ls /usr/share/zoneinfo
108  Serviços essenciais
  108.1  date   hwclock
  108.2  logger "mensagem"   tail /var/log/messages   dmesg
109  Rede
  109.1  ip addr   ip route   cat /etc/services   cat /etc/hosts
  109.3  ping -c 3 127.0.0.1   ip link   netstat -tln
110  Segurança
  110.1  find / -perm -4000 2>/dev/null   passwd -l aluno   chage -l aluno   last   w   lsof
  110.2  cat /etc/login.defs   ulimit -a

Sem internet: a rede externa fica bloqueada nesta máquina.
FIM
'''.replace("__PKG__", AJUDA_PKG), 0o755)

if os.path.exists(P("/usr/sbin/sshd")):
    subprocess.run(["mount", "--bind", "/dev", P("/dev")], check=True)
    try:
        subprocess.run(["chroot", out, "/usr/bin/ssh-keygen", "-A"], check=True, stdout=subprocess.DEVNULL)
    finally:
        subprocess.run(["umount", P("/dev")], check=True)
    cfg = P("/etc/ssh/sshd_config")
    t = open(cfg).read()
    if "KernelBase" not in t:
        t += "\n# KernelBase: laboratório local\nPermitRootLogin yes\nPasswordAuthentication yes\nUseDNS no\n"
        open(cfg, "w").write(t)
subprocess.run(["chroot", out, "/bin/sh", "-c", "echo root:kernelbase | chpasswd"], check=True)

# CentOS 7 vem com o rsyslog lendo do journald; sem systemd, ele precisa do /dev/log
rc = P("/etc/rsyslog.conf")
if distro == "centos" and os.path.exists(rc):
    t = open(rc).read()
    t = t.replace("$ModLoad imjournal", "#$ModLoad imjournal").replace("$OmitLocalLogging on", "$OmitLocalLogging off")
    t = t.replace("$IMJournalStateFile", "#$IMJournalStateFile")
    open(rc, "w").write(t)
    lc = P("/etc/rsyslog.d/listen.conf")
    if os.path.exists(lc):
        os.remove(lc)

# arquivo escondido para a missão de busca (104.7)
write("/var/lib/kernelbase/.estudo/2026/segredo-lpic.txt", "Você achou o arquivo escondido.\n")

# fstab de exemplo comentado (104.3)
fstab = P("/etc/fstab")
old = open(fstab).read() if os.path.exists(fstab) else ""
if "/mnt/dados" not in old:
    with open(fstab, "a") as f:
        f.write("\n# Exemplo para praticar montagem (descomente depois de criar /dev/sda1):\n# /dev/sda1  /mnt/dados  ext4  defaults  0  2\n")

# tira as configurações de proxy usadas só na montagem da imagem
for f in ("/etc/apt/apt.conf.d/99kb-proxy", "/etc/ssl/kb-proxy-ca.crt", "/usr/sbin/policy-rc.d"):
    if os.path.lexists(P(f)):
        os.remove(P(f))
if os.path.exists(P("/etc/yum.conf")):
    y = open(P("/etc/yum.conf")).read().replace("proxy=http://127.0.0.1:8081\n", "")
    open(P("/etc/yum.conf"), "w").write(y)

# limpa caches que só ocupam espaço
for p in ("/var/cache/yum", "/var/cache/apt/archives", "/var/lib/apt/lists"):
    if os.path.isdir(P(p)):
        for f in glob.glob(P(p) + "/*"):
            if os.path.isfile(f) and not f.endswith("lock"):
                os.remove(f)

subprocess.run(["chroot", out, "depmod", "-a", kver], check=True)
import re as _re
CP437 = set("áéíóúçàâêôÇüÉ")
for _f in ("/etc/motd", "/usr/local/bin/kb-ajuda", "/var/lib/kernelbase/.estudo/2026/segredo-lpic.txt"):
    _t = open(P(_f), encoding="utf-8").read()
    _bad = sorted({c for c in _t if ord(c) > 127 and c not in CP437})
    assert not _bad, (_f, _bad)
print("%s: kernel %s, %d comandos ligados em /usr/local/bin" % (distro, kver, len(linked)))
print("ligados:", " ".join(sorted(linked)))
