# Como as imagens do laboratório são montadas

O `lab.html` liga um Debian 12 ou um CentOS 7 (i386) no navegador com o
emulador [v86](https://github.com/copy/v86). Os arquivos de cada sistema ficam
em `lab/flat/` (compactados com zstd) e a árvore de cada um em
`lab/debian-fs.json` e `lab/centos-fs.json`.

## Origem

- Debian 12: rootfs i386 do `debuerreotype/docker-debian-artifacts` (branch `dist-i386`).
- CentOS 7.9: rootfs i386 do `CentOS/sig-cloud-instance-images` (branch `CentOS-7-i386`).
- Kernel, initramfs e módulos: Alpine `linux-virt` da branch `lab-assets`.
- Pacotes de estudo instalados com apt (deb.debian.org) e yum (vault.centos.org).

## Passos

1. Extraia o rootfs, instale os pacotes num chroot (veja a lista em `build_image.py`).
2. `build_image.py <debian|centos> <rootfs> <arvore-alpine> <saida>`: kernel do
   Alpine, init próprio (`/usr/sbin/kb-init`), ferramentas extras em
   `/opt/kernelbase`, motd e `kb-ajuda`.
3. `mkflat.py <saida> <nome> <dir> <chroot-com-zstd>`: gera o `<nome>-fs.json` e os
   arquivos `.bin.zst`.
4. `mklab.py lab.html`: gera a página com as missões de `missions.json`.

## Como as missões são corrigidas

O init deixa uma shell de root ligada à porta serial (`ttyS0`). A página manda
o comando de verificação de cada missão por ela e lê a resposta
(`__KB_OK_n__` ou `__KB_NO_n__`). O aluno usa o terminal do `tty1`.
