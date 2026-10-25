import json, sys, urllib.parse
tpl = open('/home/claude/build/lab_template.html', encoding='utf-8').read()
M = json.load(open('/home/claude/build/missions.json', encoding='utf-8'))
for m in M:
    for k in ('id','obj','topic','title','goal','learn','hint','solution','check'):
        assert k in m, (m.get('id'), k)
js = json.dumps(M, ensure_ascii=False).replace('</', '<\\/')
wa = "https://wa.me/5583933003583?text=" + urllib.parse.quote("Olá! Vim pelo laboratório da KernelBase e quero saber da turma de 12 de fevereiro do curso LPIC-1.")
out = tpl.replace('%%MISSIONS%%', js).replace('%%NMISS%%', str(len(M))).replace('%%WA%%', wa)
assert '%%' not in out
open(sys.argv[1], 'w', encoding='utf-8').write(out)
print('lab.html:', len(out), 'bytes,', len(M), 'missões')
