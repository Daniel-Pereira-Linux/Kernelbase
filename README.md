# KernelBase

Site: **[kernelbase.com.br](https://kernelbase.com.br)**

A KernelBase oferece um curso de LPIC-1 em 3 meses (todo o conteúdo dos exames
101-500 e 102-500, aulas às sextas e sábados às 20h). A página inicial
(`index.html`) apresenta o curso. A central de documentação do Kernel Linux
continua no ar em `kernel.html`.

## Documentação do Kernel

Central de documentação em português para contribuir com o Kernel Linux —
um guia prático de como traduzir, revisar e enviar patches de documentação
via `git send-email`, além de acompanhar patches recentes da lista
`linux-doc` e notícias da comunidade, tudo em um só lugar.

## Estrutura

```
index.html               página do curso LPIC-1 (landing)
kernel.html              documentação do Kernel, patches e status (abas)
lab.html                 página do laboratório
css/style.css             estilos e temas
js/app.js                 interatividade de kernel.html (abas, temas, busca, dados)
kernel-releases.json      status atual do kernel (kernel.org)
patches.json               patches recentes (lore.kernel.org, lista linux-doc)
news.json                   notícias traduzidas (Phoronix, LWN, Planet Kernel, ...)
scripts/                    scripts Python que alimentam os JSON acima
.github/workflows/sync.yml  atualiza os JSON automaticamente a cada 30 min
```

O site é 100% estático (HTML/CSS/JS puro, sem build step; a landing é um único `index.html` com CSS e JS embutidos) e hospedado via
GitHub Pages a partir da branch `gh-pages`. Os três arquivos `.json` na raiz
são lidos diretamente pelo `js/app.js` no navegador.

## Automação

O workflow [`sync.yml`](.github/workflows/sync.yml) roda a cada 30 minutos e:

1. busca a versão atual do kernel em kernel.org (`scripts/fetch_kernel_releases.py`);
2. busca patches recentes no lore.kernel.org (`scripts/fetch_patches.py`);
3. busca e traduz notícias de RSS de várias fontes (`scripts/fetch_news.py`);
4. commita apenas os arquivos que realmente mudaram.

Cada uma dessas três etapas é isolada (`continue-on-error`) e o commit roda
sempre (`if: always()`) — assim, se uma fonte externa cair ou bloquear
temporariamente, as outras continuam sincronizando normalmente.

## Rodando localmente

```bash
python3 -m http.server 8000
# abra http://localhost:8000
```

Para testar os scripts de sincronização:

```bash
python3 scripts/fetch_kernel_releases.py
python3 scripts/fetch_patches.py
pip install feedparser deep-translator beautifulsoup4
python3 scripts/fetch_news.py
```

## Contribuindo

O próprio site, na aba **Documentação**, é o guia passo a passo de como
enviar uma contribuição de tradução para o Kernel Linux.
