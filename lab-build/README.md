# Como as imagens do laboratório são montadas

A seção **Laboratório** do `index.html` liga um Debian 12 ou um CentOS 7 (i386)
no navegador com o emulador [v86](https://github.com/copy/v86). O runtime do v86
fica em `lab/v86/`. Os arquivos de cada sistema (compactados com zstd) e a árvore
de cada um (`debian-fs.json`, `centos-fs.json`) ficam na branch **`lab-files`**,
servida por raw.githubusercontent.com num commit fixo. Assim o GitHub Pages não
precisa publicar os ~300 MB do laboratório. O `sw.js` guarda esses arquivos no
navegador do aluno, e a página baixa em paralelo os arquivos do boot
(`boot_files.json`) antes de ligar a máquina.

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
4. Publique o diretório gerado na branch `lab-files` e grave o hash do commit
   em `labfiles.sha`.
5. `mklab_section.py`: gera a seção do laboratório (com as missões de
   `missions.json`), que o gerador da página inicial insere em `#laboratorio`.

`mkinitrd.py` monta a initramfs mínima (busybox + 4 módulos do 9p), que
substitui a do Alpine e corta o boot pela metade.

## Como as missões são corrigidas

O init deixa uma shell de root ligada à porta serial (`ttyS0`). A página manda
o comando de verificação de cada missão por ela e lê a resposta
(`__KB_OK_n__` ou `__KB_NO_n__`). O aluno usa o terminal do `tty1`.
