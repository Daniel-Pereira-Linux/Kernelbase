# Converte lab_template.html numa seção embutida (#laboratorio) para a página inicial.
import re, json, urllib.parse
s = open('/home/claude/build/lab_template.html', encoding='utf-8').read()
M = json.load(open('/home/claude/build/missions.json', encoding='utf-8'))

css = s[s.index('<style>') + 7:s.index('</style>')]
# remove blocos que pertencem só à página isolada
DROP = {':root', ':focus-visible', '.wrap', '.skip', '.top', '.top-in', '.brand', '.brand-mark', '.nav', '.intro', '.lede', '.facts'}
DROP_EXACT = {'*', 'html', 'body', 'a', 'h1'}
def prefix_rules(block):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', block):
        sel, body = m.group(1).strip(), m.group(2)
        tok = re.match(r'[.#:]?[\w-]*', sel).group(0)
        if sel in DROP_EXACT or tok in DROP or sel.startswith('footer') or sel.startswith('body.d-centos'):
            continue
        sels = []
        for part in sel.split(','):
            part = part.strip()
            if part.startswith('body.'):
                part = part.replace('body.', '#laboratorio.', 1)
            elif part.startswith('html'):
                continue
            else:
                part = '#laboratorio ' + part
            sels.append(part)
        if sels:
            out.append(','.join(sels) + '{' + body + '}')
    return '\n'.join(out)
res = []
i = 0
while i < len(css):
    j = css.find('@media', i)
    if j == -1:
        res.append(prefix_rules(css[i:])); break
    res.append(prefix_rules(css[i:j]))
    k = css.index('{', j); depth = 1; p = k + 1
    while depth:
        if css[p] == '{': depth += 1
        elif css[p] == '}': depth -= 1
        p += 1
    inner = css[k + 1:p - 1]
    pr = prefix_rules(inner)
    if pr.strip():
        res.append(css[j:k] + '{' + pr + '}')
    i = p
lab_css = ('#laboratorio{--mint:#59F0A8;--accent:var(--cyan);--mono:"IBM Plex Mono",ui-monospace,Menlo,Consolas,monospace}\n'
           '#laboratorio.d-centos{--accent:var(--magenta)}\n' + '\n'.join(res))
lab_css = lab_css.replace('#laboratorio #laboratorio', '#laboratorio')
lab_css = lab_css.replace('#laboratorio.running #laboratorio .work', '#laboratorio.running .work')

# marcação: escolha + área de trabalho
body = s[s.index('<section class="pick"'):s.index('</main>')]
body = body.replace('<h2 id="pick-h">Escolha o sistema</h2>', '<h3 id="pick-h" class="lab-pick-h">Escolha o sistema</h3>')
body = body.replace('<h2 id="m-h">Missões</h2>', '<h3 id="m-h" class="lab-m-h">Missões</h3>')

js = s[s.index('<script>') + 8:s.rindex('</script>')]
js = js.replace('%%MISSIONS%%', json.dumps(M, ensure_ascii=False).replace('</', '<\\/'))
LABBASE = "https://raw.githubusercontent.com/Daniel-Pereira-Linux/kernel-docs-br/%s/" % open('/home/claude/build/labfiles.sha').read().strip()
BF = json.load(open('/home/claude/build/boot_files.json'))
fsd = {}
for _n in ('debian', 'centos'):
    _d = json.load(open('/home/claude/build/labout/%s-fs.json' % _n))
    _boot = {}
    def _w(es, p):
        for e in es:
            full = p + '/' + e[0]
            if isinstance(e[6], list): _w(e[6], full)
            elif full in ('/boot/vmlinuz-virt', '/boot/initramfs-virt'): _boot[full] = e[6]
    _w(_d['fsroot'], '')
    first = [_boot['/boot/vmlinuz-virt'], _boot['/boot/initramfs-virt']]
    import os as _os
    rest = [f for f in BF[_n] if f not in first and _os.path.exists('/home/claude/build/labout/flat/' + f)]
    fsd[_n] = first + rest
js = js.replace('%%LABBASE%%', LABBASE).replace('%%BOOTFILES%%', json.dumps(fsd))
js = js.replace('document.body.classList.remove("d-debian", "d-centos");', '$("laboratorio").classList.remove("d-debian", "d-centos");')
js = js.replace('document.body.classList.add(DISTROS[d].cls, "running");', '$("laboratorio").classList.add(DISTROS[d].cls, "running");')
js = js.replace('document.body.classList.remove("running");', '$("laboratorio").classList.remove("running");')
js = js.replace('  window.scrollTo({ top: 0 });\n', '  $("laboratorio").scrollIntoView({ block: "start" });\n')
js = js.replace('document.querySelectorAll(".card")', 'document.querySelectorAll("#laboratorio .card")')
js = js.replace('document.querySelectorAll(".btn-check,.btn-type")', 'document.querySelectorAll("#laboratorio .btn-check,#laboratorio .btn-type")')
js = js.replace('const $ = (id) => document.getElementById(id);', 'const $ = (id) => document.getElementById(id);')
assert 'document.body' not in js
js = '(function(){\n' + js + '\n})();'

head = '''<section class="block lab-app d-debian" id="laboratorio">
  <div class="wrap">
    <div class="sec-head">
      <h2>Pratique num Linux de verdade, aqui mesmo</h2>
      <p>Escolha Debian 12 ou CentOS 7. A máquina liga dentro desta página, roda só no seu navegador e é apagada quando a sessão de 30 minutos termina. São %d missões da LPIC-1, corrigidas na hora.</p>
    </div>
''' % len(M)
body = body.replace('<section class="pick" aria-labelledby="pick-h">\n  <div class="wrap">', '<div class="pick" aria-labelledby="pick-h">\n  <div>', 1)
body = body.replace('<section class="work" aria-label="Laboratório">\n  <div class="wrap">', '<div class="work" aria-label="Laboratório">\n  <div>', 1)
body = body.replace('</section>', '</div>')
section = head + body + '  </div>\n</section>\n'
extra_css = '''
#laboratorio .pick{padding:0}
#laboratorio .lab-pick-h{font-family:var(--display);font-weight:700;font-size:1.4rem;margin-bottom:1rem}
#laboratorio .lab-m-h{font-family:var(--display);font-weight:700;font-size:1.35rem;letter-spacing:-.02em}
#laboratorio .work{padding:0}
#laboratorio .btn:hover{transform:none}
'''
json.dump({'css': lab_css + extra_css, 'html': section, 'js': js}, open('/home/claude/build/lab_section.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('ok', len(lab_css), len(section), len(js))
