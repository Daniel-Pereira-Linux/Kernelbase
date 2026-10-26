#!/usr/bin/env python3
"""Gera index.html (landing do curso LPIC-1 da KernelBase, versão colorida) e
valida o programa contra a lista oficial de objetivos da LPIC-1 v5.0."""
import sys, html, re, urllib.parse

OUT = sys.argv[1]

WA_NUMBER = "5583933003583"
EMAIL = "danielmaraboo@gmail.com"
WA_TEXT = "Olá! Quero saber da turma de 7 de novembro do curso LPIC-1 da KernelBase."
WA_URL = "https://wa.me/%s?text=%s" % (WA_NUMBER, urllib.parse.quote(WA_TEXT))

OFFICIAL_101 = ["101.1","101.2","101.3","102.1","102.2","102.3","102.4","102.5","102.6",
                "103.1","103.2","103.3","103.4","103.5","103.6","103.7","103.8",
                "104.1","104.2","104.3","104.5","104.6","104.7"]
OFFICIAL_102 = ["105.1","105.2","106.1","106.2","106.3","107.1","107.2","107.3",
                "108.1","108.2","108.3","108.4","109.1","109.2","109.3","109.4",
                "110.1","110.2","110.3"]

WEEKS = [
 (1, ("Hardware e processo de boot", ["101.1","101.2"]),
     ("Boot targets, desligamento e layout de disco", ["101.3","102.1"])),
 (2, ("Gerenciador de boot e bibliotecas compartilhadas", ["102.2","102.3"]),
     ("Pacotes Debian e RPM", ["102.4","102.5"])),
 (3, ("Virtualização e a linha de comando", ["102.6","103.1"]),
     ("Filtros de texto e gerenciamento de arquivos", ["103.2","103.3"])),
 (4, ("Pipes, redirecionamento e processos", ["103.4","103.5"]),
     ("Prioridades de processos e expressões regulares", ["103.6","103.7"])),
 (5, ("Editor vi e particionamento de disco", ["103.8","104.1"]),
     ("Integridade e montagem de sistemas de arquivos", ["104.2","104.3"])),
 (6, ("Permissões e propriedade de arquivos", ["104.5"]),
     ("Links, FHS e localização de arquivos", ["104.6","104.7"])),
 (7, ("Ambiente do shell", ["105.1"]),
     ("Scripts simples", ["105.2"])),
 (8, ("Usuários e grupos", ["107.1"]),
     ("Agendamento de tarefas e localização", ["107.2","107.3"])),
 (9, ("Hora do sistema e logs", ["108.1","108.2"]),
     ("E-mail (MTA) e impressão", ["108.3","108.4"])),
 (10, ("Protocolos de internet e rede persistente", ["109.1","109.2"]),
      ("Diagnóstico de rede e DNS cliente", ["109.3","109.4"])),
 (11, ("Administração de segurança e segurança do host", ["110.1","110.2"]),
      ("Criptografia de dados: SSH e GPG", ["110.3"])),
 (12, ("Interface gráfica, desktops e acessibilidade", ["106.1","106.2","106.3"]),
      ("Simulados e revisão dos dois exames", [])),
]
MONTHS = [
 (1, "Sistema, pacotes e linha de comando", 1, 4),
 (2, "Discos, permissões, shell e administração", 5, 8),
 (3, "Serviços, rede, segurança e simulados", 9, 12),
]

# ---------- validação ----------
codes = [c for _, a, b in WEEKS for c in a[1] + b[1]]
assert len(WEEKS) == 12
assert len(codes) == len(set(codes)), "objetivo repetido"
assert set(codes) == set(OFFICIAL_101 + OFFICIAL_102), set(codes) ^ set(OFFICIAL_101 + OFFICIAL_102)
assert len(OFFICIAL_101) == 23 and len(OFFICIAL_102) == 19
assert {c for w, a, b in WEEKS if w <= 6 for c in a[1] + b[1]} == set(OFFICIAL_101)
sessions = len(WEEKS) * 2
assert sessions == 24

def esc(t): return html.escape(t, quote=True)
def exam(w): return "101" if w <= 6 else "102"

# ---------- datas ----------
from datetime import date, timedelta
START = date(2026, 11, 7)
assert START.weekday() == 5          # 07/11/2026 cai num sábado
MES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
def dia(d): return "%s de %s" % ("1º" if d.day == 1 else d.day, MES[d.month-1])
def curto(d): return "%d/%d" % (d.day, d.month)
def sexta(w): return START + timedelta(days=7*(w-1))   # 1ª aula da semana (sábado)
def sabado(w): return sexta(w) + timedelta(days=6)     # 2ª aula da semana (sexta seguinte)
assert sexta(1) == date(2026,11,7) and sabado(12) == date(2027,1,29)
DN = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]

# ---------- grade das 24 aulas ----------
def grade():
    out = ['<div class="grid24" role="group" aria-label="Calendário das 24 aulas: clique em uma aula para ver a semana">']
    out.append('<span class="g-lab" aria-hidden="true"></span>')
    for w, _, _ in WEEKS:
        out.append('<span class="g-wk e%s" aria-hidden="true">%d<small>%s</small></span>' % (exam(w), w, curto(sexta(w))))
    for idx, day in ((1, "Sábado"), (2, "Sexta")):
        out.append('<span class="g-lab" aria-hidden="true">%s</span>' % ("Sáb" if idx == 1 else "Sex"))
        for w, sex, sab in WEEKS:
            title, objs = (sex if idx == 1 else sab)
            d = sexta(w) if idx == 1 else sabado(w)
            tip = "%d, %s, %s: %s" % (w, day.lower(), dia(d), title)
            lab = "Semana " + tip + (" (objetivos %s)" % ", ".join(objs) if objs else "")
            out.append('<a class="cell e%s" href="#semana-%d" data-tip="%s" aria-label="%s"></a>'
                       % (exam(w), w, esc(tip), esc(lab)))
    out.append('</div>')
    out.append('<ul class="legend">'
               '<li><span class="sw e101"></span><span>Exame 101-500: semanas 1 a 6</span></li>'
               '<li><span class="sw e102"></span><span>Exame 102-500: semanas 7 a 12</span></li></ul>')
    return "\n".join(out)

def cell(day, title, objs, d):
    if objs:
        o = '<span class="obj" aria-label="Objetivos %s">%s</span>' % (", ".join(objs), ", ".join(objs))
    else:
        o = '<span class="obj">Revisão</span>'
    return ('<div class="slot"><p class="slot-day">%s, %s, 20h</p><p class="slot-title">%s</p>%s</div>'
            % (day, dia(d), html.escape(title, quote=False), o))

def programa():
    out = []
    for m, name, a, b in MONTHS:
        out.append('<section class="month" aria-labelledby="mes%d">' % m)
        out.append('<h3 class="month-title" id="mes%d"><span class="month-n">Mês %d</span> %s <span class="month-range">%s a %s</span></h3>'
                   % (m, m, html.escape(name, quote=False), dia(sexta(a)), dia(sabado(b))))
        out.append('<ol class="weeks">')
        for w, sex, sab in WEEKS:
            if not (a <= w <= b): continue
            if w == 7:
                out.append('<li class="marker" role="presentation">Aqui termina o conteúdo do exame 101-500 (%s). Daqui em diante, o 102-500.</li>' % dia(sabado(6)))
            out.append('<li class="week e%s" id="semana-%d"><p class="week-n">Semana %d</p>%s%s</li>'
                       % (exam(w), w, w, cell("Sábado", *sex, sexta(w)), cell("Sexta", *sab, sabado(w))))
        out.append('</ol></section>')
    return "\n".join(out)

CSS = r"""
:root{
  --night:#090C24; --deep:#10153B; --panel:#151B4A; --ink:#EEF0FF; --muted:#A3ABDD; --rule:#262E6B;
  --cyan:#22E5F0; --magenta:#FF3EA5; --yellow:#FFD60A; --cobalt:#4C6FFF; --violet:#7A4DFF;
  --display:"Bricolage Grotesque","Trebuchet MS",system-ui,sans-serif;
  --serif:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;scroll-padding-top:5.5rem;background:var(--night)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
body{background:var(--night);color:var(--ink);font-family:var(--serif);font-size:1.125rem;line-height:1.65;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:var(--cyan);text-underline-offset:.2em}
a:hover{color:#8CF3F8}
:focus-visible{outline:3px solid var(--yellow);outline-offset:3px;border-radius:3px}
.wrap{width:min(1120px,100% - 2.5rem);margin-inline:auto}
.skip{position:absolute;left:-999px;top:.5rem;background:var(--yellow);color:var(--night);padding:.5rem .9rem;z-index:30;font-family:var(--display);font-weight:600}
.skip:focus{left:.5rem}
.nw{white-space:nowrap}

/* topo */
.top{position:sticky;top:0;z-index:20;background:rgba(9,12,36,.82);backdrop-filter:blur(10px);border-bottom:1px solid var(--rule)}
.top-in{display:flex;align-items:center;gap:1.5rem;min-height:4.1rem}
.top .btn-sm{white-space:nowrap}
@media (max-width:1100px){.nav{gap:1.1rem;font-size:.92rem}}
.brand{font-family:var(--display);font-weight:800;font-size:1.4rem;letter-spacing:-.03em;color:var(--ink);text-decoration:none;display:inline-flex;align-items:center;gap:.55rem}
.brand:hover{color:var(--ink)}
.brand-mark{width:.85rem;height:.85rem;background:linear-gradient(135deg,var(--cyan),var(--magenta));display:inline-block}
.nav{display:flex;gap:1.5rem;margin-left:auto;font-family:var(--display);font-weight:500;font-size:.98rem}
.nav a{color:var(--ink);text-decoration:none;padding:.3rem 0;border-bottom:2px solid transparent;white-space:nowrap}
.nav a:hover{border-color:var(--magenta);color:var(--ink)}
.btn{display:inline-block;font-family:var(--display);font-weight:700;font-size:1.05rem;line-height:1;text-decoration:none;padding:1rem 1.5rem;border-radius:6px;background:var(--yellow);color:var(--night);border:2px solid var(--yellow);transition:transform .15s,box-shadow .15s,background .15s}
.btn:hover{background:#FFE24A;border-color:#FFE24A;color:var(--night);box-shadow:0 10px 30px -8px rgba(255,214,10,.55);transform:translateY(-2px)}
.btn-sm{font-size:.95rem;padding:.7rem 1.05rem}
.btn-ghost{background:transparent;color:var(--ink);border-color:var(--cobalt)}
.btn-ghost:hover{background:var(--cobalt);border-color:var(--cobalt);color:#fff;box-shadow:0 10px 30px -8px rgba(76,111,255,.6)}
@media (prefers-reduced-motion:reduce){.btn{transition:none}.btn:hover{transform:none}}

/* hero */
.hero{position:relative;padding:clamp(2.5rem,6vw,5rem) 0 clamp(2.5rem,5vw,4rem);overflow:hidden;isolation:isolate}
.hero::before,.hero::after{content:"";position:absolute;z-index:-1;border-radius:50%;filter:blur(90px);opacity:.55;pointer-events:none}
.hero::before{width:34rem;height:34rem;left:-12rem;top:-10rem;background:var(--violet)}
.hero::after{width:30rem;height:30rem;right:-8rem;top:2rem;background:var(--magenta);opacity:.3}
.hero-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:clamp(2rem,5vw,4.5rem);align-items:center}
h1{font-family:var(--display);font-weight:800;font-size:clamp(2.7rem,1.1rem + 5.8vw,5.3rem);line-height:.96;letter-spacing:-.04em;text-wrap:balance}
.lede{margin-top:1.5rem;font-size:clamp(1.15rem,1rem + .6vw,1.4rem);line-height:1.5;max-width:34rem;color:#DDE1FF}
.by{margin-top:1.1rem;font-family:var(--display);font-size:1.02rem;color:var(--muted);max-width:34rem}
.by strong{color:var(--ink);font-weight:600}
.cta-row{margin-top:2rem;display:flex;flex-wrap:wrap;gap:.9rem;align-items:center}
.cta-note{margin-top:1rem;color:var(--muted);font-size:.98rem}

/* terminal */
.term{position:relative;background:#050816;color:var(--yellow);border-radius:12px;padding:1.2rem 1.3rem 1.5rem;font-family:var(--mono);font-size:.9rem;line-height:1.8;min-height:17.5rem;border:1px solid transparent;
  background-image:linear-gradient(#050816,#050816),linear-gradient(135deg,var(--cyan),var(--violet) 55%,var(--magenta));background-origin:border-box;background-clip:padding-box,border-box;
  box-shadow:0 0 0 1px rgba(34,229,240,.08),0 30px 80px -20px rgba(122,77,255,.55)}
.term-bar{color:var(--muted);font-size:.8rem;margin-bottom:.9rem;padding-bottom:.7rem;border-bottom:1px solid var(--rule)}
.ln{display:block;overflow-wrap:anywhere}
.ln .ok{color:#59F0A8}
.ln .dim{color:#8F98D6}
.ln .c1{color:var(--cyan)}
.ln .c2{color:var(--magenta)}
.js .ln{opacity:0}
.js .ln.on{opacity:1}
.cursor{display:inline-block;width:.6em;height:1.05em;background:var(--yellow);vertical-align:text-bottom;margin-left:.15em;animation:blink 1.1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.cursor{animation:none}}

/* grade das 24 aulas */
.cal{margin-top:clamp(2.5rem,5vw,4rem)}
.cal-title{font-family:var(--display);font-weight:600;font-size:1.1rem;color:var(--muted);margin-bottom:1rem}
.grid24{display:grid;grid-template-columns:3.2rem repeat(12,minmax(0,1fr));gap:.4rem;align-items:center}
.g-lab{font-family:var(--display);font-size:.85rem;color:var(--muted)}
.g-wk{font-family:var(--display);font-weight:700;font-size:.85rem;text-align:center;font-variant-numeric:tabular-nums}
.g-wk.e101{color:var(--cyan)}
.g-wk.e102{color:var(--magenta)}
.cell{position:relative;display:block;height:2.6rem;border-radius:5px;text-decoration:none;transition:transform .15s,box-shadow .15s}
.cell.e101{background:var(--cyan);box-shadow:0 0 0 0 rgba(34,229,240,.0)}
.cell.e102{background:var(--magenta)}
.cell:hover,.cell:focus-visible{transform:translateY(-3px)}
.cell.e101:hover,.cell.e101:focus-visible{box-shadow:0 8px 22px -4px rgba(34,229,240,.75)}
.cell.e102:hover,.cell.e102:focus-visible{box-shadow:0 8px 22px -4px rgba(255,62,165,.75)}
.cell::after{content:"Semana " attr(data-tip);position:absolute;z-index:5;bottom:calc(100% + .6rem);left:50%;transform:translateX(-50%);width:max-content;max-width:15rem;background:var(--ink);color:var(--night);font-family:var(--display);font-weight:600;font-size:.85rem;line-height:1.3;padding:.5rem .7rem;border-radius:5px;opacity:0;pointer-events:none;transition:opacity .12s}
.cell:hover::after,.cell:focus-visible::after{opacity:1}
.js .cell{opacity:.14}
.js .cell.on{opacity:1}
.js .cell{transition:opacity .35s,transform .15s,box-shadow .15s}
@media (prefers-reduced-motion:reduce){.js .cell{transition:none}.cell{transition:none}}
.legend{list-style:none;display:flex;flex-wrap:wrap;gap:.4rem 2rem;margin-top:1.1rem;font-family:var(--display);font-size:.95rem;color:var(--muted)}
.legend li{display:flex;align-items:center;gap:.55rem}
.sw{width:.9rem;height:.9rem;border-radius:3px;display:inline-block}
.sw.e101{background:var(--cyan)}
.sw.e102{background:var(--magenta)}

/* seções */
section.block{padding:clamp(3rem,6vw,5.5rem) 0;border-top:1px solid var(--rule)}
h2{font-family:var(--display);font-weight:700;font-size:clamp(1.95rem,1.2rem + 2.5vw,3.1rem);line-height:1.04;letter-spacing:-.03em;text-wrap:balance}
.sec-head{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.3fr);gap:2rem;align-items:end;margin-bottom:2.5rem}
.sec-head p{color:var(--muted);max-width:36rem}
h3{font-family:var(--display);font-weight:600;letter-spacing:-.01em}

/* como funciona */
.facts{display:grid;grid-template-columns:1fr 1fr;gap:0 3rem}
.fact{padding:1.15rem 0;border-top:1px solid var(--rule);display:grid;grid-template-columns:8.5rem 1fr;gap:1rem}
.fact dt{font-family:var(--display);font-weight:600;color:var(--cyan);font-size:1rem}
.fact dd{font-size:1.1rem;color:#DDE1FF}

/* programa */
.sum{display:flex;flex-wrap:wrap;gap:.5rem 2.5rem;margin-bottom:2.5rem;font-family:var(--display);font-size:1.05rem;color:var(--muted)}
.sum strong{font-weight:800;font-size:2rem;color:var(--ink);margin-right:.25rem;letter-spacing:-.03em}
.month{margin-top:3rem}
.month-title{font-size:1.6rem;display:flex;flex-wrap:wrap;align-items:baseline;gap:.4rem 1rem;padding-bottom:.9rem;border-bottom:2px solid var(--rule)}
.month-n{color:var(--yellow);font-weight:800}
.weeks{list-style:none}
.week{display:grid;grid-template-columns:7.5rem minmax(0,1fr) minmax(0,1fr);gap:1rem 2rem;padding:1.4rem 0 1.4rem 1.1rem;border-bottom:1px solid var(--rule);border-left:4px solid var(--cyan);margin-top:.35rem;background:linear-gradient(90deg,rgba(34,229,240,.07),transparent 40%)}
.week.e102{border-left-color:var(--magenta);background:linear-gradient(90deg,rgba(255,62,165,.08),transparent 40%)}
.week-n{font-family:var(--display);font-weight:800;font-size:1.05rem;color:var(--cyan)}
.week.e102 .week-n{color:var(--magenta)}
.slot-day{font-family:var(--display);font-size:.95rem;color:var(--muted)}
.slot-title{font-family:var(--display);font-weight:600;font-size:1.15rem;line-height:1.25;margin:.15rem 0 .35rem}
.obj{display:block;color:var(--muted);font-size:.95rem;font-variant-numeric:tabular-nums}
.marker{list-style:none;margin:1rem 0 .6rem;padding:.9rem 1.1rem;background:linear-gradient(90deg,var(--cyan),var(--violet) 55%,var(--magenta));color:var(--night);font-family:var(--display);font-weight:700;font-size:1rem;border-radius:6px}

/* instrutor */
.who{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:clamp(1.5rem,4vw,3.5rem);align-items:start}
.mono-card{position:relative;aspect-ratio:1/1;max-width:22rem;border-radius:18px;background:linear-gradient(140deg,var(--cyan) 0%,var(--cobalt) 40%,var(--violet) 70%,var(--magenta) 100%);display:grid;place-items:center;overflow:hidden;box-shadow:0 30px 70px -25px rgba(122,77,255,.7)}
.mono-card span{font-family:var(--display);font-weight:800;font-size:clamp(5rem,14vw,9rem);letter-spacing:-.06em;color:var(--night);line-height:1}
.mono-card::before{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(9,12,36,.07) 0 2px,transparent 2px 6px)}
.who h2{margin-bottom:.4rem}
.who-role{font-family:var(--display);font-weight:600;color:var(--cyan);font-size:1.15rem;margin-bottom:1.4rem}
.creds{list-style:none;margin:1.2rem 0 0}
.creds li{display:grid;grid-template-columns:.8rem 1fr;gap:.9rem;padding:.85rem 0;border-top:1px solid var(--rule);font-size:1.08rem;line-height:1.45}
.creds li::before{content:"";width:.8rem;height:.8rem;margin-top:.45rem;border-radius:2px;background:var(--cyan)}
.creds li:nth-child(2)::before{background:var(--yellow)}
.creds li:nth-child(3)::before{background:var(--magenta)}
.who p{color:#DDE1FF}
.who-links{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.6rem}

/* faq */
.faq details{border-top:1px solid var(--rule)}
.faq details:last-child{border-bottom:1px solid var(--rule)}
.faq summary{cursor:pointer;list-style:none;font-family:var(--display);font-weight:600;font-size:1.2rem;padding:1.15rem 2.5rem 1.15rem 0;position:relative}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:.2rem;top:50%;transform:translateY(-50%);font-size:1.7rem;font-weight:400;color:var(--magenta)}
.faq details[open] summary::after{content:"\2212"}
.faq details p{padding:0 2.5rem 1.3rem 0;max-width:46rem;color:#DDE1FF}

/* chamada final */
.final{border-top:0;padding-top:0}
.final-card{border-radius:20px;padding:clamp(2rem,6vw,4.5rem);background:linear-gradient(120deg,var(--cobalt) 0%,var(--violet) 50%,var(--magenta) 100%);position:relative;overflow:hidden}
.final-card::after{content:"";position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(9,12,36,.08) 0 2px,transparent 2px 7px);pointer-events:none}
.final-card>*{position:relative;z-index:1}
.final h2{color:#fff;max-width:40rem;font-size:clamp(2.1rem,1.2rem + 3.4vw,3.8rem)}
.final p{max-width:36rem;margin-top:1rem;color:#fff;font-size:1.2rem}
.final .cta-row{margin-top:2rem}
.final .btn{background:var(--yellow);color:var(--night)}
.final a.txt{color:#fff;font-weight:600}
.final .alt{margin-top:1.4rem;font-size:1rem}

footer{padding:2.5rem 0 3rem;font-size:.98rem;color:var(--muted)}
.foot{display:flex;flex-wrap:wrap;gap:1rem 2.5rem;justify-content:space-between}
.foot nav{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem}
.foot a{color:var(--ink)}
.foot strong{color:var(--ink)}
.legal{margin-top:1.5rem;font-size:.9rem}

@media (max-width:900px){
  .hero-grid,.sec-head,.who,.facts{grid-template-columns:1fr}
  .facts{gap:0}
  .nav{display:none}
  .top .btn-sm{margin-left:auto}
  .week{grid-template-columns:1fr;gap:.9rem}
  .fact{grid-template-columns:7rem 1fr}
  .mono-card{max-width:13rem}
  .cell::after{display:none}
}
@media (max-width:480px){
  body{font-size:1.05rem}
  .term{font-size:.82rem;padding:1rem}
  .btn{width:100%;text-align:center}
  .btn-sm{width:auto}
  .grid24{grid-template-columns:2.4rem repeat(12,minmax(0,1fr));gap:.25rem}
  .cell{height:2.2rem;border-radius:3px}
  .g-wk{font-size:.72rem}
}
/* progresso de leitura */
.progress{position:fixed;left:0;top:0;height:3px;width:100%;transform-origin:0 50%;transform:scaleX(0);background:linear-gradient(90deg,var(--cyan),var(--violet),var(--magenta));z-index:40;pointer-events:none}

/* faixa de comandos */
.ticker{border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);overflow:hidden;background:var(--deep)}
.ticker-track{display:flex;width:max-content;animation:tick 55s linear infinite}
.ticker-track span{font-family:var(--mono);font-size:1.15rem;padding:1.05rem 1.6rem;display:inline-flex;align-items:center;gap:1.6rem;white-space:nowrap;color:var(--cyan)}
.ticker-track span::after{content:"";width:.5rem;height:.5rem;background:var(--rule);display:inline-block}
.ticker-track span:nth-child(3n+2){color:var(--magenta)}
.ticker-track span:nth-child(3n){color:var(--yellow)}
@keyframes tick{to{transform:translateX(-50%)}}
@media (prefers-reduced-motion:reduce){.ticker-track{animation:none;flex-wrap:wrap;width:auto}}

/* botão fixo do WhatsApp */
.wa-fab{position:fixed;right:1rem;bottom:1rem;z-index:25;display:inline-flex;align-items:center;gap:.55rem;font-family:var(--display);font-weight:700;font-size:1rem;text-decoration:none;color:var(--night);background:var(--yellow);padding:.8rem 1.1rem;border-radius:999px;box-shadow:0 12px 30px -8px rgba(255,214,10,.55)}
.wa-fab:hover{background:#FFE24A;color:var(--night)}
.wa-fab svg{width:1.3rem;height:1.3rem}

.g-wk small{display:block;font-weight:500;font-size:.7rem;color:var(--muted);font-variant-numeric:tabular-nums}
.month-range{font-family:var(--display);font-weight:500;font-size:1rem;color:var(--muted);margin-left:auto}
.start{display:flex;align-items:center;gap:1.1rem;margin-top:1.7rem}
.start-date{flex:none;border:2px solid var(--yellow);border-radius:12px;padding:.65rem 1rem .6rem;text-align:center;font-family:var(--display);line-height:1;background:rgba(255,214,10,.08)}
.start-date b{display:block;font-size:2.9rem;font-weight:800;letter-spacing:-.05em;color:var(--yellow)}
.start-date span{display:block;margin-top:.3rem;font-size:.9rem;font-weight:600;color:var(--ink)}
.start-text{font-family:var(--display);font-size:1.1rem;line-height:1.35}
.start-text strong{display:block;font-size:1.25rem;font-weight:700}
.start-text span{color:var(--cyan);font-weight:600}
@media (max-width:900px){.g-wk small{display:none}.month-range{margin-left:0;flex-basis:100%}}

/* laboratório */
.lab-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:clamp(1.5rem,4vw,3.5rem);align-items:center}
.lab-grid h2{margin-bottom:1.1rem}
.lab-grid p{color:#DDE1FF}
.lab-grid p+p{margin-top:1rem}
.lab-points{list-style:none;margin:1.3rem 0 1.3rem}
.lab-points li{display:grid;grid-template-columns:.8rem 1fr;gap:.9rem;padding:.7rem 0;border-top:1px solid var(--rule);font-size:1.05rem;line-height:1.4}
.lab-points li::before{content:"";width:.8rem;height:.8rem;margin-top:.4rem;border-radius:2px;background:var(--cyan)}
.lab-points li:nth-child(2)::before{background:var(--yellow)}
.lab-points li:nth-child(3)::before{background:var(--magenta)}
.term2{background:#050816;color:var(--yellow);border-radius:12px;padding:1.2rem 1.3rem 1.5rem;font-family:var(--mono);font-size:.92rem;line-height:1.8;border:1px solid transparent;
  background-image:linear-gradient(#050816,#050816),linear-gradient(135deg,var(--magenta),var(--violet) 45%,var(--cyan));background-origin:border-box;background-clip:padding-box,border-box;
  box-shadow:0 30px 80px -20px rgba(34,229,240,.35)}
.term2 .tl{display:block;overflow-wrap:anywhere}
.term2 .out{color:#8F98D6}
.term2 .sess{color:var(--cyan)}
@media (max-width:900px){.lab-grid{grid-template-columns:1fr}}

"""

JS = r"""
(function(){
  var t=document.querySelector('.term'); if(!t) return;
  var lines=[].slice.call(t.querySelectorAll('.ln'));
  var cells=[].slice.call(document.querySelectorAll('.cell'));
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce){
    lines.forEach(function(l){l.classList.add('on')});
    cells.forEach(function(c){c.classList.add('on')});
    return;
  }
  lines.forEach(function(l,i){ setTimeout(function(){l.classList.add('on')}, 500 + i*480); });
  var start = 500 + (lines.length-1)*480 + 150;
  // acende as 24 aulas em ordem: sexta e sábado de cada semana
  var order=[];
  for(var w=0;w<12;w++){ order.push(cells[w]); order.push(cells[12+w]); }
  order.forEach(function(c,i){ setTimeout(function(){ c.classList.add('on') }, start + i*70); });
})();
"""

JS2 = r"""

(function(){
  var el=document.getElementById('contagem'); if(!el) return;
  var alvo=new Date('2026-11-07T20:00:00-03:00').getTime();
  var ms=alvo-Date.now();
  if(ms<=0){ el.textContent='A turma já começou. Chame no WhatsApp para saber da próxima.'; return; }
  var d=Math.floor(ms/86400000);
  el.textContent = d>1 ? 'Faltam '+d+' dias para a primeira aula' : (d===1 ? 'Falta 1 dia para a primeira aula' : 'A primeira aula é hoje, às 20h');
})();
(function(){
  /* barra de progresso de leitura */
  var bar=document.querySelector('.progress');
  if(bar){
    var tick=false;
    function upd(){ var h=document.documentElement; var m=h.scrollHeight-h.clientHeight; bar.style.transform='scaleX('+(m>0?Math.min(1,h.scrollTop/m):0)+')'; tick=false; }
    window.addEventListener('scroll',function(){ if(!tick){ tick=true; requestAnimationFrame(upd);} },{passive:true});
    upd();
  }

})();
"""


PAGE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script>document.documentElement.className+=' js';</script>
<title>KernelBase: curso de LPIC-1 em 3 meses</title>
<meta name="description" content="Curso de LPIC-1 em 3 meses com Daniel Pereira, mantenedor da tradução pt_BR do Kernel Linux. Todo o conteúdo dos exames 101-500 e 102-500, em 24 aulas, toda sexta e sábado às 20h. A turma começa em 7 de novembro de 2026.">
<meta property="og:title" content="KernelBase: curso de LPIC-1 em 3 meses">
<meta property="og:description" content="Todo o conteúdo dos exames 101-500 e 102-500 da LPIC-1, em 24 aulas, toda sexta e sábado às 20h. Turma começa em 7 de novembro de 2026.">
<meta property="og:url" content="https://kernelbase.com.br/">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta name="theme-color" content="#090C24">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%2322E5F0'/%3E%3Cstop offset='1' stop-color='%23FF3EA5'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='100' height='100' rx='18' fill='url(%23g)'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=IBM+Plex+Mono:wght@400;500&family=Source+Serif+4:ital,opsz,wght@0,8..60,400..700;1,8..60,400&display=swap" rel="stylesheet">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Course","name":"Curso LPIC-1 em 3 meses","description":"Preparação para os exames 101-500 e 102-500 da LPIC-1, com 24 aulas às sextas e sábados às 20h.","provider":{"@type":"Organization","name":"KernelBase","url":"https://kernelbase.com.br/"},"instructor":{"@type":"Person","name":"Daniel Pereira"},"inLanguage":"pt-BR","hasCourseInstance":{"@type":"CourseInstance","startDate":"2026-11-07","endDate":"2027-05-01"}}
</script>
<style>%%CSS%%</style>
</head>
<body>
<a class="skip" href="#conteudo">Pular para o conteúdo</a>
<div class="progress" aria-hidden="true"></div>

<header class="top">
  <div class="wrap top-in">
    <a class="brand" href="#inicio"><span class="brand-mark" aria-hidden="true"></span>KernelBase</a>
    <nav class="nav" aria-label="Principal">
      <a href="#inicio">Torne-se especialista</a>
      <a href="noticias.html">Notícias</a>
      <a href="#laboratorio">Laboratório</a>
      <a href="#instrutor">Instrutor</a>
      <a href="kernel.html#docs">Docs do Kernel</a>
    </nav>
    <a class="btn btn-sm" href="%%WA%%" target="_blank" rel="noopener">Entrar na turma</a>
  </div>
</header>

<main id="conteudo">

<section class="hero" id="inicio">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        <h1>Prepare-se para a LPIC-1 em 3 meses</h1>
        <p class="lede">Todo o conteúdo dos exames 101-500 e 102-500, em 24 aulas. Toda sexta e sábado, às 20h (horário de Brasília).</p>
        <div class="start">
          <div class="start-date" aria-hidden="true"><b>7</b><span>nov 2026</span></div>
          <p class="start-text"><strong>A turma começa em 7 de novembro de 2026</strong><span id="contagem">Primeira aula num sábado, às 20h</span></p>
        </div>
        <p class="by">Com <strong>Daniel Pereira</strong>, mantenedor da tradução pt_BR da documentação do Kernel Linux.</p>
        <div class="cta-row">
          <a class="btn" href="%%WA%%" target="_blank" rel="noopener">Entrar na turma de novembro</a>
          <a class="btn btn-ghost" href="#programa">Ver o programa</a>
        </div>
        <p class="cta-note"><strong>R$ 250</strong> no Pix ou no cartão de crédito.</p>
      </div>
      <div class="term" aria-hidden="true">
        <p class="term-bar">kernelbase tty1</p>
        <span class="ln"><span class="ok">[  OK  ]</span> Carregando exame <span class="c1">101-500</span> <span class="dim">semanas 1 a 6</span></span>
        <span class="ln"><span class="ok">[  OK  ]</span> Carregando exame <span class="c2">102-500</span> <span class="dim">semanas 7 a 12</span></span>
        <span class="ln"><span class="ok">[  OK  ]</span> Montando horário <span class="dim">sexta e sábado, 20h</span></span>
        <span class="ln"><span class="ok">[  OK  ]</span> Iniciando 24 aulas</span>
        <span class="ln"><span class="ok">[  OK  ]</span> Primeira aula <span class="dim">7 de novembro</span></span>
        <span class="ln">kernelbase login: aluno<span class="cursor"></span></span>
      </div>
    </div>
    <div class="cal">
      <p class="cal-title">As 24 aulas do curso. Clique em uma para ver a semana.</p>
      %%GRADE%%
    </div>
  </div>
</section>

<div class="ticker" aria-hidden="true"><div class="ticker-track"><span>ls</span><span>cp</span><span>find</span><span>tar</span><span>grep</span><span>sed</span><span>chmod</span><span>chown</span><span>ln</span><span>mount</span><span>fdisk</span><span>mkfs</span><span>fsck</span><span>systemctl</span><span>journalctl</span><span>dpkg</span><span>apt</span><span>rpm</span><span>useradd</span><span>crontab</span><span>ip</span><span>ping</span><span>ss</span><span>dig</span><span>ssh</span><span>gpg</span><span>vi</span><span>ps</span><span>nice</span><span>dd</span><span>lsblk</span><span>lspci</span><span>ls</span><span>cp</span><span>find</span><span>tar</span><span>grep</span><span>sed</span><span>chmod</span><span>chown</span><span>ln</span><span>mount</span><span>fdisk</span><span>mkfs</span><span>fsck</span><span>systemctl</span><span>journalctl</span><span>dpkg</span><span>apt</span><span>rpm</span><span>useradd</span><span>crontab</span><span>ip</span><span>ping</span><span>ss</span><span>dig</span><span>ssh</span><span>gpg</span><span>vi</span><span>ps</span><span>nice</span><span>dd</span><span>lsblk</span><span>lspci</span></div></div>

<section class="block" id="como-funciona">
  <div class="wrap">
    <div class="sec-head">
      <h2>Como o curso funciona</h2>
      <p>Um calendário fixo, do primeiro ao último dia, para você organizar a semana e estudar sem perder o ritmo.</p>
    </div>
    <dl class="facts">
      <div class="fact"><dt>Duração</dt><dd>3 meses, em 12 semanas: de 7 de novembro de 2026 a 29 de janeiro de 2027.</dd></div>
      <div class="fact"><dt>Aulas</dt><dd>24 aulas, uma na sexta e outra no sábado de cada semana, às 20h (horário de Brasília).</dd></div>
      <div class="fact"><dt>Conteúdo</dt><dd>Os 42 objetivos oficiais da LPIC-1: 23 do exame 101-500 e 19 do 102-500.</dd></div>
      <div class="fact"><dt>Ordem</dt><dd>As semanas 1 a 6 fecham o exame 101-500. As semanas 7 a 12 cobrem o 102-500 e terminam com simulados.</dd></div>
      <div class="fact"><dt>Certificação</dt><dd>A LPIC-1 exige aprovação nos dois exames, aplicados pelo LPI.</dd></div>
      <div class="fact"><dt>Início</dt><dd>7 de novembro de 2026, um sábado, às 20h.</dd></div>
      <div class="fact"><dt>Valor</dt><dd>R$ 250, no Pix ou no cartão de crédito. Para garantir a vaga, chame no WhatsApp.</dd></div>
    </dl>
  </div>
</section>

<section class="block" id="programa">
  <div class="wrap">
    <div class="sec-head">
      <h2>Torne-se especialista</h2>
      <p>O programa do curso, semana a semana. Cada aula mostra os objetivos oficiais do exame que ela cobre, para você acompanhar o que já viu e o que falta.</p>
    </div>
    <p class="sum"><span><strong>12</strong>semanas</span><span><strong>24</strong>aulas</span><span><strong>42</strong>objetivos oficiais</span></p>
    %%PROGRAMA%%
  </div>
</section>

%%LABSECTION%%

<section class="block" id="instrutor">
  <div class="wrap who">
    <div class="mono-card" aria-hidden="true"><span>DP</span></div>
    <div>
      <h2>Daniel Pereira</h2>
      <p class="who-role">Instrutor e fundador da KernelBase</p>
      <p>Daniel é mantenedor da tradução para português brasileiro da documentação do Kernel Linux e da localização pt_BR do Git.</p>
      <ul class="creds">
        <li>Mantenedor da tradução pt_BR da documentação do Kernel Linux</li>
        <li>Mantenedor da localização pt_BR do Git</li>
        <li>Engenheiro de sistemas, com foco em infraestrutura</li>
      </ul>
      <p style="margin-top:1.2rem">Esse trabalho é público: o guia de como contribuir com o Kernel, os patches recentes e o código do site estão abertos para qualquer pessoa ver.</p>
      <div class="who-links">
        <a class="btn btn-ghost btn-sm" href="kernel.html#docs">Documentação do Kernel</a>
        <a class="btn btn-ghost btn-sm" href="kernel.html#patches">Patches recentes</a>
        <a class="btn btn-ghost btn-sm" href="https://github.com/Daniel-Pereira-Linux/kernel-docs-br" target="_blank" rel="noopener">Código no GitHub</a>
      </div>
    </div>
  </div>
</section>

<section class="block" id="duvidas">
  <div class="wrap">
    <div class="sec-head">
      <h2>Dúvidas frequentes</h2>
      <p>Não achou a sua? Pergunte pelo WhatsApp.</p>
    </div>
    <div class="faq">
      <details><summary>Quantas provas tem a LPIC-1?</summary><p>Duas: a 101-500 e a 102-500. Para ganhar a certificação, você precisa passar nas duas, em qualquer ordem, dentro de um prazo de 5 anos.</p></details>
      <details><summary>Onde faço as provas?</summary><p>Em centros de testes da Pearson VUE ou online, com supervisão (OnVUE).</p></details>
      <details><summary>Preciso de alguma certificação antes?</summary><p>Não. A LPIC-1 é o primeiro nível da trilha Linux do LPI.</p></details>
      <details><summary>Qual é o horário das aulas?</summary><p>Todas as sextas e todos os sábados, às 20h, no horário de Brasília.</p></details>
      <details><summary>Quando começa a turma e quanto custa?</summary><p>A primeira aula é no sábado, 7 de novembro de 2026, às 20h (horário de Brasília). O curso custa R$ 250, no Pix ou no cartão de crédito. Para garantir a vaga, chame a KernelBase no WhatsApp.</p></details>
    </div>
  </div>
</section>

<section class="block final" id="entrar">
  <div class="wrap">
    <div class="final-card">
      <h2>Entre na turma de novembro</h2>
      <p>A primeira aula é em 7 de novembro de 2026. O valor é R$ 250, no Pix ou no cartão de crédito. Chame no WhatsApp para garantir o seu lugar.</p>
      <div class="cta-row">
        <a class="btn" href="%%WA%%" target="_blank" rel="noopener">Falar no WhatsApp</a>
      </div>
      <p class="alt">Prefere e-mail? Escreva para <a class="txt" href="mailto:%%EMAIL%%">%%EMAIL%%</a>.</p>
    </div>
  </div>
</section>

</main>

<footer>
  <div class="wrap">
    <div class="foot">
      <p><strong>KernelBase</strong><br>Curso de LPIC-1 e documentação aberta do Kernel Linux.</p>
      <nav aria-label="Rodapé">
        <a href="#inicio">Torne-se especialista</a>
        <a href="noticias.html">Notícias</a>
        <a href="#laboratorio">Laboratório</a>
        <a href="kernel.html#docs">Documentação do Kernel</a>
        <a href="kernel.html#patches">Patches</a>
        <a href="https://github.com/Daniel-Pereira-Linux/kernel-docs-br" target="_blank" rel="noopener">Código-fonte</a>
        <a href="https://github.com/Daniel-Pereira-Linux/kernel-docs-br/issues" target="_blank" rel="noopener">Reportar problema</a>
      </nav>
    </div>
    <p class="legal">LPI e LPIC-1 são marcas do Linux Professional Institute. © 2026 KernelBase.</p>
  </div>
</footer>

<a class="wa-fab" href="%%WA%%" target="_blank" rel="noopener" aria-label="Falar no WhatsApp"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4 3h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/></svg>WhatsApp</a>
<script>%%JS%%</script>
</body>
</html>
"""

import json as _json
_LAB = _json.load(open("/home/claude/build/lab_section.json", encoding="utf-8"))
page = (PAGE.replace("%%LABSECTION%%", _LAB["html"]).replace("%%CSS%%", CSS + _LAB["css"]).replace("%%JS%%", JS + JS2 + _LAB["js"])
            .replace("%%GRADE%%", grade()).replace("%%PROGRAMA%%", programa())
            .replace("%%WANUM%%", WA_NUMBER).replace("%%WA%%", WA_URL).replace("%%EMAIL%%", EMAIL))

# evita quebra de linha dentro de "LPIC-1", "101-500" e "102-500" no texto visível
head, rest = page.split("<main", 1)
body, tail = rest.rsplit("<script>", 1)
parts = re.split(r"(<[^>]*>)", body)
parts = [x if x.startswith("<") else re.sub(r"(LPIC-1|101-500|102-500)", r'<span class="nw">\1</span>', x) for x in parts]
page = head + "<main" + "".join(parts) + "<script>" + tail

open(OUT, "w", encoding="utf-8").write(page)
print("ok:", OUT, len(page), "bytes;", sessions, "aulas;", len(set(codes)), "objetivos;",
      page.count('class="cell '), "células")
