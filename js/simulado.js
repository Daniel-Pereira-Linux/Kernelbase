/* Motor dos simulados da KernelBase: simulado.html?id=101.1 carrega simulados/101.1.json */
(function () {
  var root = document.getElementById('sim-app');
  if (!root) return;
  var id = new URLSearchParams(location.search).get('id') || '';
  if (!/^[0-9]{3}\.[0-9]{1,2}$/.test(id)) { fail('Simulado não encontrado.'); return; }

  var data, ordem, i, acertos, erros, respondida;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function embaralhar(a) { a = a.slice(); for (var k = a.length - 1; k > 0; k--) { var j = Math.floor(Math.random() * (k + 1)); var t = a[k]; a[k] = a[j]; a[j] = t; } return a; }
  function fail(msg) { root.innerHTML = '<div class="sim-empty">' + esc(msg) + ' <a href="simulados.html">Voltar aos simulados</a></div>'; }

  fetch('simulados/' + id + '.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw 0; return r.json(); })
    .then(function (d) {
      data = d;
      document.title = d.id + ' ' + d.titulo + ' | Simulados | KernelBase';
      document.getElementById('sim-title').textContent = d.id + ' ' + d.titulo;
      document.getElementById('sim-sub').textContent = d.questoes.length + ' questões · Peso ' + d.peso + ' · Fonte: ' + d.fonte;
      inicio();
    })
    .catch(function () { fail('Não consegui carregar este simulado.'); });

  function inicio() {
    root.innerHTML =
      '<div class="sim-card sim-start">' +
      '<p>São <strong>' + data.questoes.length + ' questões</strong> de múltipla escolha, em ordem aleatória. ' +
      'Depois de cada resposta você vê se acertou e a explicação. No final aparece o seu resultado e a revisão do que errou.</p>' +
      '<button class="btn" type="button" id="sim-go">Começar simulado</button></div>';
    document.getElementById('sim-go').onclick = comecar;
  }

  function comecar() {
    ordem = embaralhar(data.questoes.map(function (q) {
      return { p: q.p, e: q.e, o: embaralhar(q.o.map(function (t, k) { return { t: t, ok: k === q.a }; })) };
    }));
    i = 0; acertos = 0; erros = [];
    questao();
  }

  function questao() {
    var q = ordem[i]; respondida = false;
    var pct = Math.round(i / ordem.length * 100);
    root.innerHTML =
      '<div class="sim-progress" role="progressbar" aria-valuemin="0" aria-valuemax="' + ordem.length + '" aria-valuenow="' + i + '"><i style="width:' + pct + '%"></i></div>' +
      '<div class="sim-card">' +
      '<p class="sim-count">Questão ' + (i + 1) + ' de ' + ordem.length + ' <span>' + acertos + ' acerto' + (acertos === 1 ? '' : 's') + '</span></p>' +
      '<h2 class="sim-q" tabindex="-1">' + esc(q.p) + '</h2>' +
      '<div class="sim-opts">' + q.o.map(function (o, k) {
        return '<button type="button" class="sim-opt" data-k="' + k + '"><b>' + 'ABCD'[k] + '</b><span>' + esc(o.t) + '</span></button>';
      }).join('') + '</div>' +
      '<div class="sim-fb" hidden></div></div>';
    root.querySelector('.sim-q').focus({ preventScroll: true });
    Array.prototype.forEach.call(root.querySelectorAll('.sim-opt'), function (b) {
      b.onclick = function () { responder(+b.dataset.k); };
    });
  }

  function responder(k) {
    if (respondida) return;
    respondida = true;
    var q = ordem[i], certo = q.o[k].ok;
    if (certo) acertos++; else erros.push({ q: q, k: k });
    Array.prototype.forEach.call(root.querySelectorAll('.sim-opt'), function (b, n) {
      b.disabled = true;
      if (q.o[n].ok) b.classList.add('is-ok');
      else if (n === k) b.classList.add('is-bad');
    });
    var fb = root.querySelector('.sim-fb');
    var ultima = i === ordem.length - 1;
    fb.innerHTML =
      '<p class="sim-verdict ' + (certo ? 'ok' : 'bad') + '">' + (certo ? 'Correto!' : 'Incorreto.') + '</p>' +
      '<p>' + esc(q.e) + '</p>' +
      '<button class="btn" type="button" id="sim-next">' + (ultima ? 'Ver resultado' : 'Próxima questão') + '</button>';
    fb.hidden = false;
    var nx = document.getElementById('sim-next');
    nx.onclick = function () { if (ultima) resultado(); else { i++; questao(); window.scrollTo({ top: root.offsetTop - 90 }); } };
    nx.focus({ preventScroll: true });
  }

  function resultado() {
    var n = ordem.length, pct = Math.round(acertos / n * 100);
    var msg = pct >= 80 ? 'Excelente! Você domina este subtópico.' : pct >= 60 ? 'Bom resultado. Revise os erros abaixo e tente de novo.' : 'Vale reler o conteúdo do subtópico e refazer o simulado.';
    root.innerHTML =
      '<div class="sim-card sim-result">' +
      '<p class="sim-score"><strong>' + acertos + '</strong> de ' + n + ' <span>(' + pct + '%)</span></p>' +
      '<p>' + msg + '</p>' +
      '<div class="sim-actions"><button class="btn" type="button" id="sim-again">Refazer simulado</button>' +
      '<a class="sim-link" href="simulados.html">Voltar aos simulados</a></div></div>' +
      (erros.length ? '<h2 class="sim-rev-h">Revisão dos erros</h2>' + erros.map(function (x) {
        var certa = x.q.o.filter(function (o) { return o.ok; })[0].t;
        return '<div class="sim-card sim-rev"><h3>' + esc(x.q.p) + '</h3>' +
          '<p class="sim-yours">Sua resposta: ' + esc(x.q.o[x.k].t) + '</p>' +
          '<p class="sim-right">Correta: ' + esc(certa) + '</p>' +
          '<p>' + esc(x.q.e) + '</p></div>';
      }).join('') : '');
    document.getElementById('sim-again').onclick = function () { comecar(); window.scrollTo({ top: root.offsetTop - 90 }); };
    window.scrollTo({ top: root.offsetTop - 90 });
  }

  document.addEventListener('keydown', function (ev) {
    if (!ordem || ev.altKey || ev.ctrlKey || ev.metaKey) return;
    var k = '1234'.indexOf(ev.key);
    if (k < 0) k = 'abcd'.indexOf(ev.key.toLowerCase());
    if (k >= 0 && !respondida && root.querySelector('.sim-opt')) responder(k);
  });
})();
